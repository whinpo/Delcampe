
import sys, getopt
import logging
import os
import pprint
from requests_html import HTMLSession
import wget
import time
import re
import locale
import requests
from lxml import html

# Function convert second into day
# hours, minutes and seconds
def ConvertSectoDay(n):
    days = n // (24 * 3600)
    n = n % (24 * 3600)
    hours = n // 3600
    n %= 3600
    minutes = n // 60
    n %= 60
    seconds = n
    retour='{} jours {} heures {} minutes {} secondes'.format(days,hours,minutes,seconds)
    return(retour)

def usage():
	print('{} [item_number]: snipe pour Delcampe'.format(sys.argv[0]))


def main():
    try:
        item_number=sys.argv[1]

        # on passe en fr pour simplifier les calculs sur les prix et dates
        locale.setlocale( locale.LC_ALL, 'fr_FR.UTF-8' )
        session = HTMLSession()

        USERNAME="YYYY"
        PASSWORD="XXXXXX"
        DELCAMPE="https://www.delcampe.net"
        LOGIN_URL="{}/fr/my-account/login_check".format(DELCAMPE)
        SEARCH_URL="{}/fr/collections/search/by/number?marketplace_item_search_by_number[id]=".format(DELCAMPE)
        # session = requests.session()

        # Get login csrf token
        result = session.get(LOGIN_URL)
        tree = html.fromstring(result.text)
        authenticity_token = list(set(tree.xpath("//input[@name='user_login[_token]']/@value")))[0]
        # print(authenticity_token)

        payload = {
        "user_login[nickname]": USERNAME,
        "user_login[password]": PASSWORD,
        "_remember_me": "on",
        "user_login[_token]": authenticity_token
        }
        # print(payload)
        #nom du user loggé : /html/body/header/div[1]/div/ul/li[2]/ul/li/a/span
        #
        # Perform login
        result = session.post(LOGIN_URL, data = payload, headers = dict(referer = LOGIN_URL))
        logged=result.html.xpath('/html/body/header/div[1]/div/ul/li[2]/ul/li/a/span/@title')[0]

        # on contrôle que le user est bien connecté
        try :
        	if logged == USERNAME:
        		print('{} connecté sur Delcampe'.format(logged))
        except:
        	exit('Erreur connexion')

        #item_number="1081788043"
        url='{}"{}"'.format(SEARCH_URL,item_number)
        result = session.get(url, headers = dict(referer = url))

        try:
            # que l'objet soit vendu ou pas on a ces infos
            rech_libelle='//*[@data-item-title-{}]/text()'.format(item_number)
            libelle=result.html.xpath(rech_libelle)[0]
            print(libelle)
            print(url)
            offres=result.html.xpath('//*[@data-tab-bids]/text()')[0]
            print(offres)
            devise=result.html.xpath('//*[@itemprop="priceCurrency"]/@content')[0]
            # on enlève le symbole euro et on convertit en numérique via locale pour la , et le .
            prix=locale.atof(result.html.xpath('//*[@class="price"]/text()')[0][:-2])
            print('Prix atteint : {} {}'.format(prix,devise))

            try:
                # si il n'y a pas de bid-box, la vente est finie

                # prix_actuel=locale.atof(result.html.xpath('//*[@id="bid-box"]//*[@class="price"]/text()')[0][:-2])
                fin_encheres=time.ctime(int(result.html.xpath('//*[@data-ws-item-date-end]/@value')[0]))
                print("Objet {} toujours en vente. Voir {}".format(item_number,url))

                temps_restant=ConvertSectoDay(int(result.html.xpath('//*[@data-remaining]/@data-remaining')[0]))
                pas_des_encheres=locale.atof(result.html.xpath('//*[@id="bid-box"]//@data-min-bid-step')[0])/1000
                enchere_mini=prix+pas_des_encheres
                url_form_encheres='{}{}'.format(DELCAMPE,result.html.xpath('//*[@id="bid-box"]//*[@name="marketplace_item_buy"]/@action')[0])
                print('Pas des enchères : {}'.format(pas_des_encheres))
                print('Prix minimum : {}'.format(enchere_mini))
                print(url_form_encheres)
                print('Fin enchères : {}'.format(fin_encheres))
                print('  soit : {}'.format(temps_restant))

            except:
                print("La vente de l'objet {} est terminée. Voir {}".format(item_number,url))

        except:
            print("L'objet {} n'existe pas".format(item_number))

        finally:
            session.close()
            print('Session fermée')
    except:
        usage()
if __name__ == '__main__':
    main()
