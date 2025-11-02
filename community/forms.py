from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    """Form for creating community posts"""
    
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

