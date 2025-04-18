from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': 'Type your message...',
                'rows': 1,
                'class': 'chat-textarea'
            }),
        }

    def save(self, commit=True, sender=None, receiver=None):
      message = super().save(commit=False)
      message.sender = sender
      message.receiver = receiver
      if commit:
        message.save()
      return message
