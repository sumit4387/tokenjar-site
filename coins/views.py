from django.shortcuts import render
from django.views import View
from coins.models import Coins
from django.http import Http404


# Create your views here.
class CoinListing(View):
    template = 'coins/index.html'

    def get(self, request, *args, **kwargs):
        coins = Coins.objects.exclude(name='').order_by('name')

        return render(request, self.template, {'coins': coins})


class Followed(View):
    template = 'coins/followed.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template, {})


class CoinDetail(View):
    template = 'coins/token.html'

    def get(self, request, symbol, *args, **kwargs):
        try:
            token_detail = Coins.objects.get(symbol=symbol)
        except:
            raise Http404

        return render(request, self.template, {'token_detail' :token_detail})