from django import forms
from .models import Messageing

class MessageForm(forms.ModelForm):
    class Meta:
        model = Messageing
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter your message here'}),
        }

