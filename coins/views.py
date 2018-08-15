from django.shortcuts import render
from django.views import View

# Create your views here.
class CoinListing(View):
    template = 'coins/index.html'

    def get(self, request, *args, **kwargs):

        return render(request, self.template, {})


class Followed(View):
    template = 'coins/followed.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template, {})


class CoinDetail(View):
    template = 'coins/token.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template, {})