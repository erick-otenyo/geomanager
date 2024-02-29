from django.urls import path

from geomanager.views import (
    boundary_landing_view,
    AdditionalBoundaryIndexView,
    AdditionalBoundaryCreateView, AdditionalBoundaryEditView, AdditionalBoundaryDeleteView
)

urls = [
    path('boundary-view/', boundary_landing_view, name='boundary_landing'),
    path('additional-boundary', AdditionalBoundaryIndexView.as_view(), name='additional_boundary_index'),
    path('additional-boundary/add', AdditionalBoundaryCreateView.as_view(), name='additional_boundary_create'),
    path('additional-boundary/edit/<int:pk>', AdditionalBoundaryEditView.as_view(),
         name='additional_boundary_edit'),
    path('additional-boundary/delete/<int:pk>', AdditionalBoundaryDeleteView.as_view(),
         name='additional_boundary_delete'),
]
