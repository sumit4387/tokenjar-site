from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import json
import requests
from coins.models import Coins

class Command(BaseCommand):

    def handle(self, *args, **options):

        print("Total Coins: " + str(Coins.objects.all().count()))
        response = requests.post("https://tokenjar.io/token/manage/query")
        response_json = json.loads(response.text)
        coins_detail = {}
        for data in response_json:
            coins_detail[data['symbol']] = data

        response1 = requests.get("https://tokenjar.io/ticker/manage/query")
        response_json1 = json.loads(response1.text)

        for data in response_json1:
            for d in data['tickers']:
                base = data['base']
                address = coins_detail[d['symbol']]['address']
                decimals = coins_detail[d['symbol']]['decimals']

                if Coins.objects.filter(symbol=d['symbol']):
                    Coins.objects.filter(symbol=d['symbol']).update(
                        name=d['name'],
                        base=base,
                        website=d['website'],
                        volumeDay=d['volumeDay'],
                        telegram=d['telegram'],
                        highDay=d['highDay'],
                        priceChangeRateDay=d['priceChangeRateDay'],
                        type=d['type'],
                        priceChangeDay=d['priceChangeDay'],
                        lowDay=d['lowDay'],
                        price=d['price'],
                        twitter=d['twitter'],
                        pair=d['pair'],
                        address=address,
                        decimals=decimals,
                    )
                else:

                    Coins.objects.create(
                        name=d['name'],
                        base=base,
                        symbol=d['symbol'],
                        website=d['website'],
                        volumeDay=d['volumeDay'],
                        telegram=d['telegram'],
                        highDay=d['highDay'],
                        priceChangeRateDay=d['priceChangeRateDay'],
                        type=d['type'],
                        priceChangeDay=d['priceChangeDay'],
                        lowDay=d['lowDay'],
                        price=d['price'],
                        twitter=d['twitter'],
                        pair=d['pair'],
                        address=address,
                        decimals=decimals,
                    )


        self.stdout.write(self.style.SUCCESS('Successfully added and updated Coins'))
        print("Total Coins: " + str(Coins.objects.all().count()))
