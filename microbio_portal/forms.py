# core/forms.py

from django import forms
from .models import Request, Report
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML


# ==========================================
# CHOICE DEFINITIONS
# ==========================================
EYE_CHOICES = (
    ('OD', 'OD (Right)'),
    ('OS', 'OS (Left)'),
    ('OU', 'OU (Both)'),
    ('NA', 'NA (Not Applicable)'),
)

SAMPLE_CHOICES = (
    ('Corneal Scraping', 'Corneal Scraping'),
    ('Other', 'Other (please specify)'),
)

DURATION_VALUE_CHOICES = [(i, str(i)) for i in range(1, 11)]
DURATION_UNIT_CHOICES = (
    ('Days', 'Days'),
    ('Weeks', 'Weeks'),
    ('Months', 'Months'),
)

MEDS_CHOICES = (
    ('Antibiotics', 'Antibiotics'),
    ('Antifungals', 'Antifungals'),
    ('Antiviral', 'Antiviral'),
    ('Steroid', 'Steroid'),
    ('Others', 'Others (please specify)'),
)

IMPRESSION_CHOICES = (
    ('Bacterial', 'Bacterial'),
    ('Fungal', 'Fungal'),
    ('Acanthamoeba', 'Acanthamoeba'),
    ('Pythium', 'Pythium'),
    ('Viral', 'Viral'),
    ('Others', 'Others'),
)

STAIN_CHOICES = (
    ('Grams', 'Grams'),
    ('KOH-CFW', 'KOH-CFW'),
    ('Others', 'Others'),
)


# ==========================================
# DOCTOR REQUEST FORM
# ==========================================
class DoctorRequestForm(forms.ModelForm):
    """
    Project Clear PoC - Doctor Form
    Section A: Patient Basics
    Section B: Clinical Details
    Section C: Impression & Upload
    """
    
    # Section A: Patient Basics
    centre_name = forms.CharField(
        max_length=100,
        label='Centre Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter clinic/centre name'})
    )
    patient_id = forms.CharField(
        max_length=50,
        label='Patient ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alphanumeric ID'})
    )
    eye = forms.ChoiceField(
        choices=EYE_CHOICES,
        label='Eye Involved',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Section B: Clinical Details
    sample = forms.ChoiceField(
        choices=SAMPLE_CHOICES,
        label='Sample Type',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    sample_other = forms.CharField(
        max_length=100,
        required=False,
        label='Other Sample Type (if selected above)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify sample type'})
    )
    
    duration_value = forms.ChoiceField(
        choices=DURATION_VALUE_CHOICES,
        label='Duration Value',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    duration_unit = forms.ChoiceField(
        choices=DURATION_UNIT_CHOICES,
        label='Duration Unit',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    on_meds = forms.BooleanField(
        required=False,
        label='Patient is on medications',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    meds = forms.MultipleChoiceField(
        choices=MEDS_CHOICES,
        required=False,
        label='Select medications',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    meds_other = forms.CharField(
        max_length=250,
        required=False,
        label='Other medications (if selected)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify other meds'})
    )
    
    # Section C: Impression & Upload
    impression = forms.ChoiceField(
        choices=IMPRESSION_CHOICES,
        label='Clinical Impression',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    stain = forms.MultipleChoiceField(
        choices=STAIN_CHOICES,
        required=False,
        label='Stain Used',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Request
        fields = ('centre_name', 'patient_id', 'eye', 'sample', 'on_meds', 'impression', 'stain', 'image')
        exclude = ('doctor', 'timestamp', 'status', 'duration', 'meds')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Patient Basics',
                Row(
                    Column('centre_name', css_class='col-md-6'),
                    Column('patient_id', css_class='col-md-6'),
                ),
                'eye',
            ),
            Fieldset(
                'Clinical Details',
                Row(
                    Column('sample', css_class='col-md-12'),
                    Column('sample_other', css_class='col-md-12'),
                ),
                Row(
                    Column('duration_value', css_class='col-md-4'),
                    Column('duration_unit', css_class='col-md-4'),
                ),
                'on_meds',
                'meds',
                'meds_other',
            ),
            Fieldset(
                'Impression & Upload',
                'impression',
                'stain',
                'image',
            ),
            Submit('submit', '📤 Submit for Analysis', css_class='btn-primary btn-lg mt-3')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Combine duration
        duration_value = cleaned_data.get('duration_value')
        duration_unit = cleaned_data.get('duration_unit')
        if duration_value and duration_unit:
            cleaned_data['duration'] = f"{duration_value} {duration_unit}"
        
        # Combine meds
        meds = cleaned_data.get('meds', [])
        meds_other = cleaned_data.get('meds_other', '').strip()
        if isinstance(meds, (list, tuple)):
            meds_str = ', '.join(meds)
        else:
            meds_str = meds or ''
        if meds_other:
            meds_str = f"{meds_str}, {meds_other}" if meds_str else meds_other
        cleaned_data['meds'] = meds_str
        
        # Combine stain
        stain = cleaned_data.get('stain', [])
        if isinstance(stain, (list, tuple)):
            cleaned_data['stain'] = ', '.join(stain)
        
        # Combine sample
        sample = cleaned_data.get('sample')
        sample_other = cleaned_data.get('sample_other', '').strip()
        if sample == 'Other' and sample_other:
            cleaned_data['sample'] = sample_other
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.duration = self.cleaned_data.get('duration', '')
        instance.meds = self.cleaned_data.get('meds', '')
        instance.stain = self.cleaned_data.get('stain', '')
        instance.sample = self.cleaned_data.get('sample', '')
        instance.on_meds = self.cleaned_data.get('on_meds', False)
        if commit:
            instance.save()
        return instance


# ==========================================
# LAB REPORT FORM
# ==========================================
class LabReportForm(forms.ModelForm):
    """
    Lab Technician form for analyzing and authorizing reports.
    """
    
    class Meta:
        model = Report
        fields = ('rc_code', 'lab_id', 'quality', 'sample_suitability', 'suitability_reason', 'report_text', 'comments', 'auth_by')
        widgets = {
            'rc_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reading Centre Code'}),
            'lab_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lab ID (Alphanumeric)'}),
            'quality': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'sample_suitability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'suitability_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Explain if sample is not suitable'}),
            'report_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter main microbiology report findings'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes (optional)'}),
            'auth_by': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('rc_code', css_class='col-md-6'),
                Column('lab_id', css_class='col-md-6'),
            ),
            Row(
                Column('quality', css_class='col-md-6'),
                Column('sample_suitability', css_class='col-md-6'),
            ),
            'suitability_reason',
            'report_text',
            'comments',
            'auth_by',
            Submit('submit', '✓ Generate Report', css_class='btn-success btn-lg mt-3')
        )
