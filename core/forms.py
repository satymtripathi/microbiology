# core/forms.py

from django import forms
from .models import Request, Report
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

# ==========================================
# DOCTOR FORM (Phase 3)
# ==========================================
class DoctorRequestForm(forms.ModelForm):
    STAIN_CHOICES = [
        ('Grams', 'Grams'),
        ('KOH-CFW', 'KOH-CFW'),
        ('Others', 'Others'),
    ]

    stain = forms.ChoiceField(
        choices=[('', '--- Select Stain ---')] + STAIN_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Stain(s) Requested'
    )
    
    class Meta:
        model = Request
        exclude = ('doctor', 'timestamp', 'status')
        labels = {
            'patient_id': 'Patient ID',
            'centre_name': 'Clinic/Centre Name',
            'eye': 'Affected Eye *',
            'sample': 'Sample Type *',
            'duration_value': 'Duration',
            'duration_unit': 'Unit *',
            'on_meds': 'Prior Medications? *',
            'meds_category': 'Medication Type',
            'meds_custom': 'Medication Name (for Others)',
            'impression': 'Clinical Impression',
            'stain': 'Stain(s) Requested',
            'image': 'Microscopy Slide Image (JPEG/PNG)',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If instance exists, pre-populate stain from stored string
        if self.instance and self.instance.pk and self.instance.stain:
            self.initial['stain'] = self.instance.stain.strip()
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('patient_id', css_class='form-group col-md-4 mb-0'),
                Column('centre_name', css_class='form-group col-md-4 mb-0'),
                Column('eye', css_class='form-group col-md-4 mb-0'),
                css_class='row mb-4'
            ),
            Row(
                Column('sample', css_class='form-group col-md-4 mb-0'),
                Column('duration_value', css_class='form-group col-md-4 mb-0'),
                Column('duration_unit', css_class='form-group col-md-4 mb-0'),
                css_class='row mb-4'
            ),
            'on_meds',
            'meds_category',
            'meds_custom',
            Row(
                Column('impression', css_class='form-group col-md-6 mb-0'),
                Column('stain', css_class='form-group col-md-6 mb-0'),
                css_class='row mb-4'
            ),
            'image',
            Submit('submit', '📤 Submit for Lab Analysis', css_class='btn-primary mt-4')
        )

# ==========================================
# LAB FORM (Phase 4)
# ==========================================
# core/forms.py (Update LabReportForm)

# ... (DoctorRequestForm definition)

class LabReportForm(forms.ModelForm):
    class Meta:
        model = Report
        # request field is handled by the view, primary_key is implicit
        exclude = ('request',) 
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Section 1: Administrative
            Row(
                Column('rc_code', css_class='form-group col-md-6 mb-0'),
                Column('lab_id', css_class='form-group col-md-6 mb-0'),
                css_class='row mb-4'
            ),
            
            # Section 2: Quality Assessment
            Row(
                Column('quality', css_class='form-group col-md-6 mb-0'),
                Column('suitability', css_class='form-group col-md-6 mb-0'),
                css_class='row mb-4'
            ),
            
            # Section 3: Interpretation
            'report_text', 
            'comments', 
            
            # Section 4: Authorization
            'auth_by',
            
            Submit('submit', '✅ Authorize & Complete Report', css_class='btn-success mt-4')
        )

    def save(self, commit=True):
        # Default save behavior for lab report
        instance = super().save(commit=commit)
        return instance