from django.shortcuts import render
from django.http import JsonResponse
from .models import Member, Team


def neo4j_test_view(request):
    team_name = 'nosql_lotr'

    team = Team.nodes.get_or_none(name=team_name)
    if not team:
        team = Team(name=team_name).save()

    names = ["Рита :)", "артём", "Свеклана"]
    ages = [20, 20, 19]

    for name, age in zip(names, ages):
        member = Member.nodes.get_or_none(name=name)
        if not member:
            member = Member(name=name, age=age).save()

        if not member.team.is_connected(team):  # type: ignore
            member.team.connect(team)  # type: ignore

    us = Member.nodes.all()
    us_list = [{"name": m.name, "age": m.age, "team": team.name} for m in us]

    return JsonResponse({
        "message": "Connected successfully!",
        "status": "success",
        "team_size": len(us),
        "members": us_list
    }, json_dumps_params={'ensure_ascii': False, 'indent': 2})