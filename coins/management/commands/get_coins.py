from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import json
import requests
from coins.models import Coins

class Command(BaseCommand):

    def handle(self, *args, **options):

        print("Total Coins: " + str(Coins.objects.all().count()))
        # response = requests.post("https://tokenjar.io/token/manage/query",data={'network': 1})
        # response = requests.post("https://tokenjar.io/token/manage/query")
        response = requests.get("https://tokenjar.io/ticker/manage/query")
        response_json = json.loads(response.text)

        for data in response_json:
            for d in data['tickers']:
                if Coins.objects.filter(symbol=d['symbol']):
                    Coins.objects.filter(symbol=d['symbol']).update(name=d['name'])
                else:
                    Coins.objects.create(name=d['name'], symbol=d['symbol'])
                break
                # print(d)

        self.stdout.write(self.style.SUCCESS('Successfully added and updated Coins'))
        print("Total Coins: " + str(Coins.objects.all().count()))
