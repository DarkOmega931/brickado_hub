from django import forms


class ArchetypeUploadForm(forms.Form):
    file = forms.FileField(
        label="Arquivo TXT ou CSV de arquétipos",
        help_text="TXT: um arquétipo por linha. CSV: coluna 1 = nome, coluna 2 (opcional) = slug.",
    )
