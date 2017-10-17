from django import forms
from .models import *

MAX_DISTANCES = ((1100, '1100bp'),
                 (2200, '2200bp'),
                 (5500, '5500bp'),
                 (-1, 'custom') # Placeholder
                 )
#['average', 'mad', 'median', 'tail_1000']
TESTS = (('average', 'Average'),
         ('mad', 'Median Absolute Deviation'),
         ('median', 'Median'),
         ('tail_1000', 'Right tail size'))
P_VALUES = ((5, '0.05'),
            (10, '0.1'),
            (20, '0.2')
            )

class EncodeParameterForm(forms.ModelForm):
    class Meta:
        model = EncodeFormModel
        fields = ['tf1', 'cell', 'method']
        widgets ={
            'cell': forms.HiddenInput(),
            'method': forms.HiddenInput(),
        }

    def __init__(self, cell, method,*args, **kwargs):
        super(EncodeParameterForm, self).__init__(*args, **kwargs)
        self.fields['cell'].initial = cell
        self.fields['method'].initial = method
        #self.fields['tf1'] = cell


class EncodeParameterForm_2(forms.Form):
    cell = forms.CharField(widget=forms.HiddenInput())
    method = forms.CharField(widget=forms.HiddenInput())

    #tf1 = forms.ChoiceField(label='TF1', max_length=50)
    #docfile = forms.FileField(
    #    label='Select a file', required=False
    #)
    max_dist = forms.IntegerField(label='Maximum distance in couples [bp]: ',
                                  min_value=0, max_value=5500,
                                  widget=forms.RadioSelect(choices=MAX_DISTANCES))
    num_min = forms.IntegerField(label='How many mindistance couples are needed?',
                                 min_value=0)
    num_min_w_tsses = forms.DecimalField(label='Fraction of couples '
                                               'colocating in a promoter?',
                                 min_value=0, max_value=1)
    which_tests = forms.MultipleChoiceField(label='Which tests do you want to use?',
                                            choices=TESTS,
                                            widget=forms.CheckboxSelectMultiple())
    min_test_num = forms.IntegerField(label='How many tests should be '
                                            'passed?',
                                 min_value=1, max_value=4)
    pvalue = forms.IntegerField(label='Individual test pvalue: ',
                                widget=forms.RadioSelect(choices=P_VALUES)
                                )


class CellMethodForm(forms.Form):
    cell = forms.ChoiceField(choices=[("hepg2", "HepG2"), ("k562", "K562")])
    method = forms.ChoiceField(choices=[("encode", "Encode"),
                                        ("upload_encode", "My data vs. Encode"),
                                        ("upload_mydata", "My data vs. my data"),
                                        ],
                               label="What to do",
                               widget=forms.RadioSelect)