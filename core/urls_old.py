# core/urls.py

from django.urls import path
from core.views import logout_user, PINLoginView

from django.views.generic.base import RedirectView
from . import views
from .views import DoctorReportListView, LabQueueListView

urlpatterns = [
    # Root Redirect: Handles the empty path (/) and redirects to login
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='root_redirect'),

    # Authentication
    path('login/', PINLoginView.as_view(), name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'), 
    
    # --- DOCTOR VIEWS (Phase 3) ---
    # 1. Submission Form
    path('doctor/submit/', views.doctor_submit_view, name='doctor_submit'),
    
    # 2. Reports Tracking
    path('doctor/reports/', DoctorReportListView.as_view(), name='doctor_reports'),

    # --- LAB VIEWS (Phase 4) ---
    # 1. Pending Queue (List)
    path('lab/queue/', LabQueueListView.as_view(), name='lab_queue'),
    
    # 2. Process Request (Detail/Creation)
    path('lab/process/<int:pk>/', views.lab_process_request, name='lab_process'), 
    
    # 3. PDF Download Path
    path('report/pdf/<int:pk>/', views.generate_report_pdf, name='generate_report_pdf'),

    # Logout
    path('logout/', logout_user, name='logout'),
]