from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Mentorados, Navigators, DisponibilidadeHorarios, Reuniao
from django.contrib import messages
from django.contrib.messages import constants
from datetime import datetime
from datetime import timedelta
from .auth import valida_token
import locale

# Create your views here.
def mentorados(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "GET":
        navigators = Navigators.objects.filter(user=request.user)
        mentorados = Mentorados.objects.filter(user=request.user)

        estagios_flat = [i[1] for i in Mentorados.estagio_choices]
        qtd_estagios = []

        for i, j in Mentorados.estagio_choices:
            qtd_estagios.append(Mentorados.objects.filter(estagio=i).count())

        return render(request, 'mentorados.html', {'estagios': Mentorados.estagio_choices,
        'navigators': navigators, 'mentorados': mentorados, 'estagios_flat': estagios_flat, 'qtd_estagios': qtd_estagios})

    elif request.method == 'POST':
        nome = request.POST.get('nome')
        foto = request.FILES.get('foto')
        estagio = request.POST.get('estagio')
        navigator = request.POST.get('navigator')

        mentorado = Mentorados(
            nome=nome,
            foto=foto,
            estagio=estagio,
            navigator_id=navigator,
            user=request.user
        )

        mentorado.save()

        messages.add_message(request, constants.SUCCESS, 'Mentorado cadastrado com sucesso.')
        return redirect('mentorados')


def reunioes(request):
    if request.method == 'GET':
        return render(request, 'reunioes.html')
    elif request.method == 'POST':
        data = request.POST.get('data')
        data = datetime.strptime(data, '%Y-%m-%dT%H:%M')

        disponibilidades = DisponibilidadeHorarios.objects.filter(mentor=request.user).filter (
            data_inicial__gte=(data - timedelta(minutes=50)),
            data_inicial__lte=(data + timedelta(minutes=50))
        )

        if disponibilidades.exists():
            messages.add_message(request, constants.ERROR, 'Você já possui uma reunião em aberto.')
            return redirect('reunioes')

        disponibilidades = DisponibilidadeHorarios(
            data_inicial=data,
            mentor=request.user

        )
        disponibilidades.save()

        messages.add_message(request, constants.SUCCESS, 'Horário disponibilizado com sucesso.')
        return redirect('reunioes')


def auth(request):
    if request.method == 'GET':
        return render(request, 'auth_mentorado.html')
    else:
        token = request.POST.get('token')

        if not Mentorados.objects.filter(token=token).exists():
            messages.add_message(request, constants.ERROR, 'Token inválido')
            return redirect('auth_mentorado')

        response = redirect('escolher_dia')
        response.set_cookie('auth_token', token, max_age=3600)
        return response

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

def escolher_dia(request):
    if not valida_token(request.COOKIES.get('auth_token')):
        return redirect('auth_mentorado')
    if request.method == 'GET':
        mentorado = valida_token(request.COOKIES.get('auth_token'))

        disponibilidades = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=datetime.now(),
            agendado=False,
            mentor=mentorado.user
        ).values_list('data_inicial', flat=True)

        datas = []
        for data in disponibilidades:
            datas.append({
                'data_formatada': data.date().strftime('%d-%m-%Y'),
                'mes': data.strftime('%B'),  # Nome do mês
                'dia_semana': data.strftime('%A'),  # Nome do dia da semana
            })

        return render(request, 'escolher_dia.html', {'datas': datas})



def agendar_reuniao(request):
    # Valida o token de autenticação do mentorado
    token = request.COOKIES.get('auth_token')
    mentorado = valida_token(token)
    if not mentorado:
        messages.add_message(request, messages.ERROR, 'Token inválido ou expirado.')
        return redirect('auth_mentorado')

    if request.method == 'GET':
        data = request.GET.get("data")
        try:
            # Converte a data da string para um objeto datetime
            data = datetime.strptime(data, '%d-%m-%Y')
        except ValueError:
            messages.add_message(request, messages.ERROR, 'Formato de data inválido.')
            return redirect('escolher_dia')

        # Filtra os horários disponíveis com base na data e no mentor
        horarios = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=data,
            data_inicial__lt=data + timedelta(days=1),
            agendado=False,
            mentor=mentorado.user
        )
        print(data)
        # Renderiza o template com os horários disponíveis
        if not horarios.exists():
            messages.add_message(request, messages.WARNING, 'Nenhum horário disponível para essa data.')
        return render(request, 'agendar_reuniao.html', {'horarios': horarios, 'tags': Reuniao.tag_choices})