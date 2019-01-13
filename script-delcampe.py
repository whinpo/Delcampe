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
		self.pages=self.get_pages()
		self.ventes=self.get_ventes()
		self.nbVentes=len(self.ventes)
		self.images=self.get_images()
		self.nbImages=len(self.images)
		#print(self.searchURL)
		print(self.pages)
		print('nb images : {0}'.format(self.nbImages))
		print('nb Ventes : {0}'.format(self.nbVentes))
	#	self.nbImages=self.get_nbImages()

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
		# on affiche en gallerie avec les thumbs (pour pouvoir avoir les zooms) et on trie par date de vente
		url='{0}/{1}/search?view=gallery&order=sale_start_datetime&view=thumbs&size={2}{3}'.format(self.urlDelcampeCollections,self.section,self.size,termURL,displayongoing)
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

			print('Nb pages : {0}'.format(nbpages))
		else:
			print('Problème. Code retour : {0}'.format(r.status_code))
		return int(nbpages)

	# retourne la liste des pages de la recherche
	def get_pages(self):
		listePages=[]

		# si on a une seule page, on met juste la requête dans le tableau
		for pages in range(0,self.nbPages):
			listePages.append('{0}&page={1}'.format(self.searchURL,pages+1))
			#print ('{0}&page={1}'.format(self.searchURL,pages+1))
		return listePages


	# retourne la liste des ventes actuelles et passées pour la recherche en question
	def get_ventes(self):

		splitted=[]
		splittedFullURL=[]
		numpage=1
		listeVentes=[]
		for page in self.pages:
			print('Récupération de la liste des ventes de la page {0}/{1}'.format(numpage,self.nbPages))
		#	print("page {0}/{1}".format(page,self.listePages))
			# on se connecte sur la page
			r = session.get(page)
			# on contrôle que la connexion est OK
			if r.status_code == 200:
				print('Lecture URL {0} : OK'.format(page))

				print('Status : {0}'.format(r.status_code))
				print('Analyse de la page en cours')
				numpage=numpage+1

				# commandes xpath pour récupérer l'ensemble des ventes, id, prix et liste des images
				listeId=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/div[@class="item-gallery"]/@id')
				listeImg=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/*//div[@class="image-container"]/div/a/@href')
				listePrix=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/*//div[@class="item-footer"]/*//div[@class="item-price"]/*/text()')
				listeVendeurs=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/div[@class="item-gallery"]/*//div[@class="option-content"]/a/@title')

				listeVentestemp={}

				print('Génération de la liste des Ventes')
				# on crée une liste listeVentestemp qui va contenir un nested dictionnary
				i=0
				for id in listeId:
					# on supprime item-
					idnum=id[5:]
					# on intialise le dict nested qui a pour clé l'id
					listeVentestemp[idnum] = {}
					# affectation du prix
					listeVentestemp[idnum]["prix"]=listePrix[i][:-2]
					# affectation du vendeur
					listeVentestemp[idnum]["vendeur"]=listeVendeurs[i]
					# on crée un tableau vide pour les images (on est obligé de les traiter à part, leur nb n'étant pas fixe)
					listeVentestemp[idnum]["images"]=[]
					i=i+1

				# on parcout listeImg et on affecte les images à "images" de l'id en question
				print('Génération de la liste des images des Ventes')
				for item in listeImg:
					# l'image est de la forme https://images-00.delcampe-static.net/img_large/auction/000/618/719/212_001.jpg
					# on prend la fin => 618/719/212, si cela commence par un 0 on l'enlève et on enlève ensuite les / pour obtenir
					# 618/719/212 => 618719212
					# cela nous permet de retrouver l'id et donc de pouvoir affecter
					num1=item[-19:-8]
					imageId='{0}{1}{2}'.format(num1[:3],num1[4:7],num1[8:11])
					#print(imageId,item)
					while imageId[0] == '0':
						imageId=imageId[1:]
					listeVentestemp[imageId]["images"].append(item)

				for id in listeVentestemp:
					listeVentes.append(vente(id,listeVentestemp[id]))
			else:
				print('Problème lecture {0} . Code retour : {1}'.format(page,r.status_code))
		return listeVentes

	# retourne les images de la recherche
	# on fait un boucle sur les images de la vente pour avoir tout dans un seul array
	def get_images(self):
		images=[]
		for ventes in self.ventes:
			for ventesimg in ventes.images:
				images.append(ventesimg)
		return images


class vente:
	def __init__(self,id,dict):
		self.id=id
		self.prix=dict['prix']
		#self.url=url
		self.vendeur=dict['vendeur']
		self.images=dict['images']
		self.nbImages=len(self.images)


	def info(self):
		print("id : {0}".format(self.id))
		print("vendeur : {0}".format(self.vendeur))
		print("prix : {0}".format(self.prix))
		print("Nb images : {0}".format(self.nbImages))
		print("images : {0}".format(self.images))

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
