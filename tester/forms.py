from django import forms
from .models import *
from .utils import get_tf_list


class EncodeParameterForm(forms.ModelForm):
    class Meta:
        model = EncodeFormModel
        fields = '__all__'
        widgets ={
            'session_id': forms.HiddenInput(),
            'cell': forms.HiddenInput(),
            'method': forms.HiddenInput(),
            'which_tests' : forms.CheckboxSelectMultiple(),
            'tf1' : forms.SelectMultiple(),
            'tf2': forms.SelectMultiple(),

        }

        labels = {
            'which_tests' : 'Which tests do you want to use?',
            'max_dist' : 'Maximum distance in couples [bp]',
            'num_min' : 'How many mindistance couples are needed?',
            'num_min_w_tsses' : 'Fraction of couples colocating in a promoter?',
            'min_test_num' : 'How many tests should be passed?',
            'pvalue' : 'Individual test pvalue',
            'tf1': 'Select one or more TFs',
            'tf2': 'Select one or more TFs',
        }


    def __init__(self, cell, method,*args, **kwargs):
        super(EncodeParameterForm, self).__init__(*args, **kwargs)
        self.fields['cell'].initial = cell
        self.fields['method'].initial = method
        self.fields['tf1'].choices = [(x,x) for x in get_tf_list(cell)]
        self.fields['tf2'].choices = [(x, x) for x in get_tf_list(cell)]
        self.fields['which_tests'].empty_label = None

    def __set_tf1__(self, tf1_list):
        self.fields['tf1'].choices = [(x,x) for x in tf1_list]

    def __set_tf2__(self, tf2_list):
        self.fields['tf2'].choices = [(x,x) for x in tf2_list]

    def __set_session_id__(self, session_id):
        self.fields['session_id'].initial = session_id

class MyDataEncodeParameterForm(forms.ModelForm):
    class Meta:
        model = MyDataEncodeFormModel
        fields = '__all__'

        widgets = {
            'cell': forms.HiddenInput(),
            'method': forms.HiddenInput(),
            'session_id' : forms.HiddenInput(),
            'upload_status' : forms.HiddenInput(),

        }

        labels = {
            'mydata' : 'Upload your dataset here',
            'which_tests' : 'Which tests do you want to use?',
            'max_dist' : 'Maximum distance in couples [bp]',
            'num_min' : 'How many mindistance couples are needed?',
            'num_min_w_tsses' : 'Fraction of couples colocating in a promoter?',
            'min_test_num' : 'How many tests should be passed?',
            'pvalue' : 'Individual test pvalue',
        }


    def set_initial_values(self, cell, method, session_id):
        self.fields['cell'].initial = cell
        self.fields['method'].initial = method
        self.fields['session_id'].initial = session_id



class CellMethodForm(forms.Form):
    cell = forms.ChoiceField(choices=[("hepg2", "HepG2"), ("k562", "K562")])
    method = forms.ChoiceField(choices=[("encode", "Encode"),
                                        ("mydata_encode", "My data vs. Encode"),
                                        ("mydata_mydata", "My data vs. my data"),
                                        ],
                               label="What to do",
                               widget=forms.RadioSelect)