from functools import reduce
from operator import or_

from django import VERSION as DJANGO_VERSION
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.exceptions import (
    ImproperlyConfigured,
    SuspiciousOperation,
)
from django.db import models
from wagtail_modeladmin.views import IndexView


def build_q_object_from_lookup_parameters(parameters):
    q_object = models.Q()
    # The original Django implementation of this method uses parameters.items()
    # which returns param_item_list as a non-list if the parameter is a single item.
    # We need to consistently have a list
    for param, param_item_list in parameters.lists():
        q_object &= reduce(or_, (models.Q((param, item)) for item in param_item_list))
    return q_object


class PatchedIndexView(IndexView):
    def get_queryset(self, request=None):
        request = request or self.request
        
        # First, we collect all the declared list filters.
        (
            self.filter_specs,
            self.has_filters,
            remaining_lookup_params,
            filters_use_distinct,
        ) = self.get_filters(request)
        
        # Then, we let every list filter modify the queryset to its liking.
        qs = self.get_base_queryset(request)
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(request, qs)
            if new_qs is not None:
                qs = new_qs
        
        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            if DJANGO_VERSION >= (5, 0):
                qs = qs.filter(
                    build_q_object_from_lookup_parameters(remaining_lookup_params)
                )
            else:
                qs = qs.filter(**remaining_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception as e:  # noqa: BLE001
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)
        
        if not qs.query.select_related:
            qs = self.apply_select_related(qs)
        
        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)
        
        # Remove duplicates from results, if necessary
        if filters_use_distinct:
            qs = qs.distinct()
        
        # Apply search results
        return self.get_search_results(request, qs, self.query)
