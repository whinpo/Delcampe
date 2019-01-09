#!/usr/bin/env python3
import sys, getopt
import logging
import os
import pprint
from pathlib import Path
from requests_html import HTMLSession
from threading import Thread
session = HTMLSession()

def usage():
	print('script-delcampe.py -s <section> -t <terme de recherche> <-n maxscreens>  [- si vendu],["section="]')
	print('section : de la forme cartes-postales/france et on peut ajouter autant de sous-sections que l''on souhaite')
	print(' 		 Pour trouver la section, il suffit d''aller sur un objet en vente et de regarder l''url')

def split(arr, size):
     arrs = []
     while len(arr) > size:
         pice = arr[:size]
         arrs.append(pice)
         arr   = arr[size:]
     arrs.append(arr)
     return arrs

def main(argv):
	global commande
	global section
	global optionS
	global term
	global optionT
	global maxscreens
	global optionM
	global vendu
	global optionV


	defaultmaxscreens=10
	term=optionC=optionS=optionT=optionM=optionV=''
	vendu=False

	try:
		opts, args = getopt.getopt(argv,"s:t:m:hv",["section=","term=","maxscreens="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt in ("-s", "--section"):
			section = arg
			optionS='-s {0}'.format(section)
		elif opt in ("-t", "--term"):
			term = arg
			optionT='-t {0}'.format(term)
		elif opt in ("-m", "--maxscreens"):
			maxscreens = arg
			if not maxscreens.isnumeric():
				print("Le nombre de screens doit être numérique")
				usage()
				sys.exit(2)
			else:
				optionM='-m {0}'.format(maxscreens)
		elif opt in ("-v", "--vendu"):
			vendu = True
			optionV='-v'


	# on contrôle que -s a bien été rempli !
	if not section:
		print('Param -s obligatoire')
		usage()
		sys.exit(2)

	# on remplit les paramètres facultatifs
	if not optionT:
		optionT=''
	if not optionM:
		optionM=''
		maxscreens=defaultmaxscreens

	commande='script-delcampe.py {0} {1} {2} {3}'.format(optionS,optionT,optionM,optionV)

class recherche:
	urlDelcampe="https://www.delcampe.net"
	urlDelcampeCollections='{0}/fr/collections'.format(urlDelcampe)

	# nombre de réponses par page
	size=480

	def __init__(self,section,term):
		self.section=section
		self.term=term
		self.searchURL=self.set_searchURL()
		self.nbPages=self.get_nbPages()
		self.listePages=self.get_listePages()
		self.listeVentes=self.get_listeVentes()

	# génere une url de la forme : https://https://www.delcampe.net/fr/collections/france/entiers-postaux/search?size=480
	# en fonction des critères de recherche
	def set_searchURL(self):
		# si on a un critère de recherche
		termURL=''
		if self.term:
			termURL='&term={0}'.format(term)

		# on veut voir les ventes cloturées
		displayongoing=''
		if vendu:
			displayongoing='&display_ongoing=closed'

		url='{0}/{1}/search?size={2}{3}'.format(self.urlDelcampeCollections,self.section,self.size,termURL,displayongoing)
		return url

	#
	def get_nbPages(self):
		print(self.searchURL)

		# on se connecte sur la page
		r = session.get(self.searchURL)

		# on contrôle que la connexion est OK
		if r.status_code == 200:
			print('Lecture URL : OK')

			# liste des ventes
			#print(r.html.xpath('//*[@id]/div/div[1]/div/a[@class="item-link"]/@href'))

			# liste des pages
			try:
				listePages=r.html.xpath('//*[@class="pag-number"]/text()')
				print('liste {0}'.format(listePages))
				nbpages=listePages[0]
			except:
				nbpages=1

			print('nbpages {0} à traiter'.format(nbpages))
		else:
			print('Problème. Code retour : {0}'.format(r.status_code))
		return int(nbpages)

	# retourne la liste des pages de la recherche
	def get_listePages(self):
		listePages=[]

		# si on a une seule page, on met juste la requête dans le tableau
		for pages in range(0,self.nbPages):
			listePages.append('{0}&page={1}'.format(self.searchURL,pages+1))
			#print ('{0}&page={1}'.format(self.searchURL,pages+1))
		return listePages


	# retourne la liste des ventes actuelles et passées pour la recherche en question
	def get_listeVentes(self):

		splitted=[]
		splittedFullURL=[]
		numpage=1

		for page in self.listePages:
			print('Récupération de la liste des ventes de la page {0}/{1}'.format(numpage,self.nbPages))
		#	print("page {0}/{1}".format(page,self.listePages))
			# on se connecte sur la page
			r = session.get(page)
			# pour avoir le lien, le vendeur et le prix
			#r.html.xpath('//*[@class="item-footer"]/*/@href|//*[@class="option-content"]/*/@title|//*[@class="item-price"]/*/text()')
			# pour le mettre dans un tableau de tuples :
			#split(r.html.xpath('//*[@class="item-footer"]/*/@href|//*[@class="option-content"]/*/@title|//*[@class="item-price"]/*/text()'),3)


			# on doit pouvoir directement créer les ventes sans repasser par la lecture de chacune de celles-ci, on a en effet tout ce qu'il faut
			#  sur la page de recherche !!!!!!
			# suite pb récupération des images et ventes mises en pub
			# Id de la vente : r.html.xpath('//*[@class="item-listing item-all-thumbs"]/div[@class="item-gallery"]/@id')
			# vendeur r.html.xpath('//*[@class="item-listing item-all-thumbs"]/div[@class="item-gallery"]/*//div[@class="option-content"]/a/@title')
			# prix r.html.xpath('//*[@class="item-listing item-all-thumbs"]/*//div[@class="item-footer"]/*//div[@class="item-price"]/*/text()')
			# images = r.html.xpath('//*[@class="item-listing item-all-thumbs"]/*//div[@class="image-content"]/a/@href')

			splitted=splitted + (split(r.html.xpath('//*[@class="item-footer"]/*/@href|//*[@class="option-content"]/*/@title|//*[@class="item-price"]/*/text()'),3))
			numpage=numpage+1
		# les href retournés sont de la forme : /fr/collections/cartes-postales/france/autres-communes-3/c-p-s-m-c-p-m-04-saint-paul-sur-ubaye-tete-de-cassoun-voir-2-scans-331934408.html'
		# on veut ajouter le https de Delcampe

		for ventes in splitted:
			print('\nVente : {0}{1}'.format(self.urlDelcampe,ventes[0]))
			print('Prix  : {0}'.format(ventes[1]))
			print('vendeur  : {0}'.format(ventes[2]))
			venteFullURL=vente('{0}{1}'.format(self.urlDelcampe,ventes[0]),ventes[1],ventes[2])
			print("listeventes : vente {0} qui a le prix {1} et vendeur : {2}".format(venteFullURL.url,venteFullURL.prix,venteFullURL.vendeur))
			splittedFullURL.append(venteFullURL)

		return splittedFullURL

class vente:
	def __init__(self,url,prix,vendeur):
		self.url=url
		self.prix=prix
		self.vendeur=vendeur
		self.listeImages=self.get_listeImages()

	# normalement pas nécessaire car on les aura directement depuis la recherche !!!!
	def get_listeImages(self):

		listeImages=[]
		print('\nAnalyse des images de la vente {0}'.format(self.url))

		# on se connecte sur la page
		r = session.get(self.url)

		# on contrôle que la connexion est OK
		if r.status_code == 200:
			print('Lecture Vente : OK')

			# liste des ventes
			#print(r.html.xpath('//*[@id]/div/div[1]/div/a[@class="item-link"]/@href'))

			# liste des images
			listeImages.append(r.html.xpath('//*[@class="slick"]/div/a/img/@src'))
			print('liste {0}'.format(listeImages))
		else:
			print('Problème. Code retour : {0}'.format(r.status_code))

		return listeImages

# génération du nom du répertoire de téléchargement
def generate_download_dir():
	global download_dir
	download_dir='{0}/{1}'.format(homedir,section)
	# si on a un critère de recherche
	if term:
		download_dir='{0}-{1}'.format(download_dir,term)
	return 	download_dir

# Création du répertoire de téléchargement
def setup_download_dir():
	global download_dir

	dirAcreer = Path(download_dir)
	if not dirAcreer.exists():
		dirAcreer.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":

	homedir='/home/whinpo/Philatélie/pompage_sites/Delcampe2'
	main(sys.argv[1:])

	#url='https://www.delcampe.net/fr/collections/search?categories%5B%5D=674&search_mode=all&excluded_terms=&is_searchable_in_descriptions=0&is_searchable_in_translations=0&term=1900+&show_type=all&display_ongoing=ongoing&started_days=&started_hours=&ended_hours=&display_only=&min_price=&max_price=&currency=all&seller_localisation=&view=thumbs&order=&country=&size=%s' s ($size)
	print(commande)

	print(section)

	# on génère la page de recherche principale
	# ~ url=generateSearchURL(section,term,vendu)
	# ~ nbpages=analyseURL(url)
	# ~ print(nbpages)

	#generate_download_dir()
	#print(download_dir)
	#print(setup_download_dir())

	recherche=recherche(section,term)
#	print(dir(recherche))
	print(recherche.searchURL)
	print(recherche.nbPages)
	print(recherche.listePages)
	print(recherche.listeVentes)


#il faudra utiliser les threads pour télécharger
#https://www.toptal.com/python/beginners-guide-to-concurrency-and-parallelism-in-python
# pour chacune des pages
## créer une liste contient toutes les url des objets en ventes sur la page
## pour chaque URL de la page
### créer une liste contient toutes les images de la page ainsi que le nom de l'image à obtenir numero_vendeur_libelle_num_image
## télécharger toutes les images avec une rupture toutes les 12.000 images

# exemple
# url = https://www.delcampe.net/fr/collections/timbres/france/1876-1898-sage-type-ii/r1752-690-sage-type-ii-n-98a-n-98c-cad-689262388.html
# nom image= r1752-690-sage-type-ii-n-98a-n-98c-cad-689262388
## liste images : # ['https://images-02.delcampe-static.net/img_small/auction/000/689/262/388_001.jpg?v=3', 'https://images-00.delcampe-static.net/img_small/auction/000/689/262/388_002.jpg?v=3', 'https://images-01.delcampe-static.net/img_small/auction/000/689/262/388_003.jpg?v=3']
## il faut supprimer le ?v=*
## le nom vient de l'url : 689262388-rolaindharcourt_r1752-690-sage-type-ii-n-98a-n-98c-cad-689262388_001 002 et 003

# liste des images d'une page : r.html.xpath('//*[@class="img-container"]/img/@src')
# vendeur : r.html.xpath('//*[@class="nickname"]/text()')[-1]
# prix : r.html.xpath('//*[@class="price"]/text()')[-1].replace('\xa0€','')
