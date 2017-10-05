from django import forms

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

class ParameterForm(forms.Form):
    tf1 = forms.CharField(label='TF1', max_length=50)
    cell = forms.CharField(label='Cell', max_length=50)
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
