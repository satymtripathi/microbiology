# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView
from django.views import View

# ReportLab PDF Imports
from reportlab.lib import colors 
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from django.http import HttpResponse 


from .models import Request, PortalUser, Report, RequestHistory
from .forms import DoctorRequestForm, LabReportForm
from .forms_login import PINLoginForm


# ==========================================
# MIXINS
# ==========================================
class DoctorRequiredMixin(UserPassesTestMixin):
    """Allows access only if the user is a Doctor."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_doctor()


class LabRequiredMixin(UserPassesTestMixin):
    """Allows access only if the user is a Lab Technician."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_lab()


# ==========================================
# LOGIN & DASHBOARD
# ==========================================
class PINLoginView(View):
    """Custom PIN-based login view."""
    template_name = 'core/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_doctor():
                return redirect('doctor_submit')
            elif request.user.is_lab():
                return redirect('lab_queue')
        form = PINLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = PINLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            pin = form.cleaned_data.get('pin')
            
            user = authenticate(request, username=username, pin=pin)
            if user is not None:
                login(request, user, backend='core.auth.PINAuthBackend')
                
                if user.is_doctor():
                    return redirect('doctor_submit')
                elif user.is_lab():
                    return redirect('lab_queue')
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
        
        return render(request, self.template_name, {'form': form})


@login_required
def dashboard_view(request):
    if request.user.is_doctor():
        return redirect('doctor_submit')
    elif request.user.is_lab():
        return redirect('lab_queue')
    return render(request, 'core/dashboard.html')


# ==========================================
# DOCTOR: SUBMIT REQUEST
# ==========================================
@login_required
@user_passes_test(lambda u: u.is_doctor(), login_url='login')
def doctor_submit_view(request):
    if request.method == 'POST':
        form = DoctorRequestForm(request.POST, request.FILES)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.doctor = request.user

            # Combine meds + other_meds
            meds_list = form.cleaned_data.get('meds', '')
            other_meds = form.cleaned_data.get('other_meds', '').strip()
            final_meds = meds_list if not other_meds else f"{meds_list}, {other_meds}" if meds_list else other_meds

            new_request.meds = final_meds
            new_request.status = 'Pending'
            new_request.save()

            # Record history entry for the new submission
            try:
                RequestHistory.objects.create(
                    request=new_request,
                    user=request.user,
                    action='Submitted',
                    note=f"Submitted by Dr. {request.user.full_name}"
                )
            except Exception:
                pass

            messages.success(request, f"Request for Patient {new_request.patient_id} submitted successfully!")
            return redirect('doctor_submit')
    else:
        form = DoctorRequestForm()

    return render(request, 'core/doctor_submit.html', {
        'form': form,
        'page_title': 'New Sample Submission'
    })


# ==========================================
# DOCTOR: REPORT LIST
# ==========================================
class DoctorReportListView(DoctorRequiredMixin, ListView):
    model = Request
    template_name = 'core/doctor_reports.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return Request.objects.filter(doctor=self.request.user).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for r in ctx['requests']:
            try:
                r.report_data = r.report
            except Report.DoesNotExist:
                r.report_data = None
            # Attach history entries (latest first) - don't assign to related set
            r.history_list = list(r.history_entries.all()[:20])
        return ctx


# ==========================================
# LAB: PENDING QUEUE
# ==========================================
class LabQueueListView(LabRequiredMixin, ListView):
    model = Request
    template_name = 'core/lab_queue.html'
    context_object_name = 'pending_requests'

    def get_queryset(self):
        return Request.objects.filter(status='Pending').order_by('timestamp')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for r in ctx['pending_requests']:
            r.history_list = list(r.history_entries.all()[:20])
        return ctx


# ==========================================
# LAB: PROCESS REQUEST
# ==========================================
@login_required
@user_passes_test(lambda u: u.is_lab(), login_url='login')
def lab_process_request(request, pk):
    request_obj = get_object_or_404(Request, pk=pk, status='Pending')

    if request.method == 'POST':
        form = LabReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.request = request_obj
            report.save()

            request_obj.status = 'Completed'
            request_obj.save()

            # Record history entry for completion
            try:
                RequestHistory.objects.create(
                    request=request_obj,
                    user=request.user,
                    action='Report Completed',
                    note=f"Report authored by {report.auth_by}"
                )
            except Exception:
                pass

            messages.success(request, f"Report for {request_obj.patient_id} completed!")
            return redirect('lab_queue')
    else:
        form = LabReportForm(initial={'auth_by': request.user.full_name})

    return render(request, 'core/lab_process.html', {
        'request_obj': request_obj,
        'form': form,
        'page_title': f'Process Request: {request_obj.patient_id}'
    })


# ==========================================
# REPORT VIEW: PDF Generation (TABLE LAYOUT)
# ==========================================
@login_required
@user_passes_test(lambda user: user.is_doctor() or user.is_lab(), login_url='login')
def generate_report_pdf(request, pk):
    """Generates a PDF report using a structured table layout."""
    
    request_obj = get_object_or_404(Request, pk=pk)
    try:
        report_obj = request_obj.report
    except Report.DoesNotExist:
        messages.error(request, "Report has not been completed yet.")
        if request.user.is_doctor():
            return redirect('doctor_reports')
        return redirect('lab_queue')

    response = HttpResponse(content_type='application/pdf')
    filename = f"Microbio_Report_{request_obj.patient_id}_{request_obj.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(response, pagesize=letter, 
                            leftMargin=0.5*72, rightMargin=0.5*72, 
                            topMargin=0.75*72, bottomMargin=0.75*72)
    
    styles = getSampleStyleSheet()
    story = []
    
    def bold(text, style=styles['Normal']):
        return Paragraph(f"<b>{text}</b>", style)

    # --- 1. Title ---
    title_style = styles['Title']
    title_style.alignment = 1
    story.append(Paragraph("Ocular Microbiology Laboratory Report", title_style))
    story.append(Spacer(1, 0.25 * 72))

    # Define Column Widths for main tables (Label, Data, Label, Data)
    col_widths_clinical = [1.5*72, 2.5*72, 1.5*72, 2.0*72]
    
    # --- 2. Patient & Clinical Details Table ---
    
    clinical_data_flat = [
        [bold("Patient & Clinical Details"), "", "", ""],
        [bold("Patient ID:"), request_obj.patient_id, bold("Centre:"), request_obj.centre_name],
        [bold("Eye:"), request_obj.eye, bold("Date Submitted:"), request_obj.timestamp.strftime('%Y-%m-%d %H:%M')],
        [bold("Sample:"), request_obj.sample, bold("Duration:"), f"{request_obj.duration} days"],
        [bold("Medications:"), request_obj.meds, bold("Stain Used:"), request_obj.stain],
        [bold("Clinical Impression:"), request_obj.impression, "", ""], 
    ]

    clinical_table = Table(clinical_data_flat, colWidths=col_widths_clinical)
    
    clinical_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 0), (3, 0)), 
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(clinical_table)
    story.append(Spacer(1, 0.25 * 72))

    # --- 3. Laboratory Interpretation Table ---
    
    report_quality = report_obj.quality if report_obj.quality else "N/A"
    report_suitability = "Yes" if report_obj.sample_suitability else "No (Specify reason below)"

    lab_data_flat = [
        [bold("Laboratory Interpretation"), "", "", ""],
        [bold("Lab ID:"), report_obj.lab_id, bold("RC Code:"), report_obj.rc_code],
        [bold("Sample Suitability:"), report_suitability, bold("Quality:"), report_quality],
    ]
    
    lab_table = Table(lab_data_flat, colWidths=col_widths_clinical)
    
    lab_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 0), (3, 0)),
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(lab_table)
    story.append(Spacer(1, 0.25 * 72))

    # --- 4. Report Text and Comments Table ---
    report_data = [
        [bold("Microbiology Report:"), Paragraph(report_obj.report_text.replace('\n', '<br/>'), styles['BodyText'])],
        [bold("Additional Comments:"), Paragraph(report_obj.comments.replace('\n', '<br/>'), styles['BodyText'])],
    ]
    
    report_table = Table(report_data, colWidths=[2.5*72, 5.0*72])
    
    report_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, 0), 6), 
        ('PADDING', (0, 1), (-1, 1), 6),
    ]))

    story.append(report_table)
    story.append(Spacer(1, 0.25 * 72)) # Added spacer before image

    # ==========================================
    # 🌟 NEW POSITION: CLINICAL IMAGE SECTION 🌟
    # ==========================================
    if request_obj.image:
        # Get the absolute path to the image file
        img_path = request_obj.image.path
        
        # Define max width for the image (Total available width is 7.5 inches)
        MAX_WIDTH = 7.0 * 72 
        
        try:
            # Create the Image flowable
            img = Image(img_path, width=MAX_WIDTH, height=MAX_WIDTH, kind='proportional')
            story.append(bold("Clinical Image:"))
            story.append(Spacer(1, 0.1 * 72))
            story.append(img)
            story.append(Spacer(1, 0.25 * 72))
        except Exception as e:
            # Handle cases where the image file might be corrupt or not found
            story.append(bold(f"Image Error: Could not load image. ({e})"))
            story.append(Spacer(1, 0.25 * 72))
    
    # --- 5. Authorization and Footer with Disclaimer ---
    story.append(Paragraph(f"<para alignment='right'><b>Authorized By:</b> {report_obj.auth_by}</para>", styles['Normal']))
    story.append(Spacer(1, 0.5 * 72))

    # Disclaimer with proper formatting
    disclaimer_style = styles['Normal'].clone('Disclaimer')
    disclaimer_style.fontSize = 7
    disclaimer_style.alignment = 4  # Justified
    
    disclaimer_text = """
    <b>DISCLAIMER:</b> This report is generated based on the images provided by the clinician and may be subject to change on review of the entire slide at the reading centre. 
    This report acts solely as a guide to a clinician for clinical correlation. The reading centre is not responsible for any complications that may arise during the treatment of the patient.
    <br/><br/>
    <i>Generated electronically by Project Clear - Ocular Microbiology Reading Centre</i>
    """
    
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    # 4. Build the PDF and return the response
    doc.build(story)
    return response

# ==========================================
# LOGOUT
# ==========================================
@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')