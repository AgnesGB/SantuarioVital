from django import forms
from .models import Usuario, RelatorioExpedicao, Cidade, Besta, Doenca, Paciente, Diagnostico, RegistroMedico, AnotacaoPessoal, Raca, Ingrediente, Remedio, RemedioIngrediente
from django.forms.widgets import DateInput
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

class DoencaForm(forms.ModelForm):
    class Meta:
        model = Doenca
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'origem': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'tratamento': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'sintomas': forms.TextInput(attrs={'class': 'input'}),
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nome', 'idade', 'raca', 'afinidade', 'fay_normal', 'cidade', 'status', 'contatos_emergencia', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'idade': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
                'max': '150'
            }),
            'raca': forms.SelectMultiple(attrs={'class': 'select'}),
            'afinidade': forms.Select(attrs={'class': 'select'}),
            'fay_normal': forms.TextInput(attrs={'class': 'input', 'placeholder': '💡 Ex: Luz, Fogo, Água, Terra, Ar, Trevas...'}),
            'cidade': forms.Select(attrs={'class': 'select'}),
            'status': forms.Select(attrs={'class': 'select'}),
            'contatos_emergencia': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'observacoes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }

class RegistroMedicoForm(forms.ModelForm):
    sintomas_observados = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea',
            'rows': 3,
            'placeholder': 'Descreva os sintomas observados'
        }),
        required=True
    )
    
    class Meta:
        model = RegistroMedico
        fields = ['paciente', 'sintomas_observados', 'observacoes', 'tratamento_aplicado']

class CidadeForm(forms.ModelForm):
    class Meta:
        model = Cidade
        fields = ['nome', 'funcao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'funcao': forms.TextInput(attrs={'class': 'input'}),
        }
        labels = {
            'nome': 'Nome da Cidade',
            'funcao': 'Função',
        }

class UsuarioCreationForm(UserCreationForm):
    nickname = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'nickname', 'password1', 'password2', 'cidade']
        widgets = {
            'cidade': forms.Select(attrs={'class': 'select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'input'})
        self.fields['nickname'].widget.attrs.update({'class': 'input'})
        self.fields['password1'].widget.attrs.update({'class': 'input'})
        self.fields['password2'].widget.attrs.update({'class': 'input'})

class RelatorioExpedicaoForm(forms.ModelForm):
    class Meta:
        model = RelatorioExpedicao
        fields = ['titulo', 'localizacao', 'descobertas', 'observacoes']

class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['sintomas', 'observacoes', 'doenca']  # Removi 'hipoteses' (já é tratado na view)
        widgets = {
            'sintomas': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 3,
                'placeholder': 'Descreva os sintomas observados'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 3,
                'placeholder': 'Anotações adicionais'
            }),
            'doenca': forms.Select(attrs={'class': 'select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna apenas 'sintomas' obrigatório
        self.fields['sintomas'].required = True
        self.fields['observacoes'].required = False  # Opcional
        self.fields['doenca'].required = False  # Opcional
        self.fields['doenca'].queryset = Doenca.objects.all()  # Lista todas as doenças

class BestaForm(forms.ModelForm):
    doenca_relacionada = forms.ModelMultipleChoiceField(
        queryset=Doenca.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False  # Isso permite que o campo fique em branco
    )
    
    class Meta:
        model = Besta
        fields = '__all__'
 
class AnotacaoPessoalForm(forms.ModelForm):
    class Meta:
        model = AnotacaoPessoal
        fields = ['titulo', 'conteudo', 'tags']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'input'}),
            'conteudo': forms.Textarea(attrs={'class': 'textarea', 'rows': 5}),
            'tags': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'palavra-chave1, palavra-chave2, ...'
            }),
        }


class RacaForm(forms.ModelForm):
    class Meta:
        model = Raca
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'longevidade': forms.TextInput(attrs={'class': 'input'}),
            'caracteristicas_fisicas': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'cor_sangue': forms.TextInput(attrs={'class': 'input'}),
            'pressao_arterial': forms.TextInput(attrs={'class': 'input'}),
            'bpm': forms.TextInput(attrs={'class': 'input'}),
            'afinidade_magica': forms.TextInput(attrs={'class': 'input'}),
            'cuidados_especiais': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'alimentacao': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'peculiaridades': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'observacoes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }


class IngredienteForm(forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'o_que_e': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'o_que_faz': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'contra_indicacoes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'reacoes_adversas': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'cuidados_ao_uso': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }


class RemedioForm(forms.ModelForm):
    class Meta:
        model = Remedio
        fields = ['nome', 'descricao', 'modo_uso', 'doencas', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'descricao': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'modo_uso': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'doencas': forms.SelectMultiple(attrs={'class': 'select'}),
            'observacoes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }


class RemedioIngredienteForm(forms.ModelForm):
    class Meta:
        model = RemedioIngrediente
        fields = ['ingrediente', 'quantidade']
        widgets = {
            'ingrediente': forms.Select(attrs={'class': 'select'}),
            'quantidade': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ex: 2 colheres, 100g, 5 gotas'
            }),
        }


# Formset para adicionar ingredientes ao remédio
RemedioIngredienteFormSet = inlineformset_factory(
    Remedio,
    RemedioIngrediente,
    form=RemedioIngredienteForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)