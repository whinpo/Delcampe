#!/usr/bin/env python3
import sys, getopt
import logging
import os
import pprint
from pathlib import Path
#import requests
from requests_html import HTMLSession
import wget
import multiprocessing
import threading
import time
import re
session = HTMLSession()

def run_process(url, output_path):
	# print('download {0} vers {1}'.format(url,output_path))
	if not os.path.isfile(output_path):
		try:
			wget.download(url, out=output_path)
		except:
			print('problème d/l {0}'.format(url))

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

# fonction pour remettre au propre les libellés des ventes
def urlify(s):
	#print('urlify s={0}'.format(s))
	# Remove all non-word characters (everything except numbers and letters)
	s = re.sub(r"[^\w\s]", '', s)
	# Replace all runs of whitespace with a single dash
	s = re.sub(r"\s+", '-', s)
	return s

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
	home="/Philatélie/pompage_sites/Delcampe2"

	# nombre de réponses par page
	size=480

	def __init__(self,section,term,closed):
		self.section=section
		self.term=term
		self.closed=closed
		self.searchURL=self.set_searchURL()
		self.nbPages=self.get_nbPages()
		self.pages=self.get_pages()
		self.ventes=self.get_ventes()
		self.nbVentes=len(self.ventes)
		self.images=self.get_images()
		self.nbImages=len(self.images)
		self.download_dir=self.set_download_dir()
		#print(self.searchURL)
		# print(self.pages)
		print('nb images : {0}'.format(self.nbImages))
		print('nb Ventes : {0}'.format(self.nbVentes))
		print('Download Dir : {0}'.format(self.download_dir))

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
		if self.closed == True:
			displayongoing='&display_ongoing=closed'
		# on affiche en gallerie avec les thumbs (pour pouvoir avoir les zooms) et on trie par date de vente
		url='{0}/{1}/search?view=gallery&order=sale_start_datetime&view=thumbs&size={2}{3}{4}'.format(self.urlDelcampeCollections,self.section,self.size,termURL,displayongoing)
		return url

	# génération du nom du répertoire de téléchargement
	def set_download_dir(self):
		# si on a un critère de recherche
		download_dir='{0}/{1}'.format(homedir,self.section)
		if term:
			download_dir='{0}/{1}'.format(download_dir,term)
		if self.closed==True:
			encours="-closed"
		else:
			encours="-en-cours"
		download_dir='{0}{2}'.format(download_dir,section,encours)

		return 	download_dir
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
				listePages=r.html.xpath('//*[@class="numbers-container"]/*/a/text()')
				print('liste {0}'.format(listePages))
				nbpages=listePages[-1:][0]
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
	# on supprime les ventes de cpaphil...
	def get_ventes(self):

		splitted=[]
		splittedFullURL=[]
		numpage=1
		listeVentes=[]
		listeVentesNettoyées=[]
		for page in self.pages:
			print('Récupération de la liste des ventes de la page {0}/{1}'.format(numpage,self.nbPages))
		#	print("page {0}/{1}".format(page,self.listePages))
			# on se connecte sur la page
			r = session.get(page)
			# on contrôle que la connexion est OK
			if r.status_code == 200:
				print('Lecture URL {0} : OK'.format(page))

				print('Status : {0}'.format(r.status_code))
				print('Analyse de la page en cours {0}'.format(page))
				numpage=numpage+1

				# commandes xpath pour récupérer l'ensemble des ventes, id, prix et liste des images
				listeId=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/div[@class="item-gallery"]/@id')
				#listeImg=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/*//div[@class="image-container"]/div/a/@href')
				listeImg=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/*//div[@class="image-content"]/a/img/@data-lazy')
				listePrix=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/*//div[@class="item-footer"]/*//div[@class="item-price"]/*/text()')
				listeVendeurs=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/div[@class="item-gallery"]/*//div[@class="option-content"]/a/@title')
				listeLibellés=r.html.xpath('//*[@class="item-listing item-all-thumbs"]/div[@class="item-gallery"]//*[@class="item-footer"]/a/@title')

				listeVentestemp={}

				print('Génération de la liste des Ventes  {0}'.format(page))
				# on crée une liste listeVentestemp qui va contenir un nested dictionnary
				i=0
				for id in listeId:
					# on supprime item-
					
					idnum=id.split('-')[1]
					# print(idnum,id)
					# print('on crée {}'.format(idnum))
					# on intialise le dict nested qui a pour clé l'id
					listeVentestemp[idnum] = {}
					# affectation libellé vente
					listeVentestemp[idnum]["libellé"]=urlify(listeLibellés[i])
					# affectation du vendeur
					listeVentestemp[idnum]["vendeur"]=listeVendeurs[i]
					# affectation du prix
					listeVentestemp[idnum]["prix"]=listePrix[i][:-2]
					# on crée un tableau vide pour les images (on est obligé de les traiter à part, leur nb n'étant pas fixe)
					listeVentestemp[idnum]["images"]=[]
					i=i+1

				# on parcout listeImg et on affecte les images à "images" de l'id en question
				print('Génération de la liste des images des Ventes  {0}'.format(page))
				# print(listeImg)
				for item in listeImg:
					# l'image est de la forme https://images-00.delcampe-static.net/img_large/auction/000/618/719/212_001.jpg?v=xx
					# on enleve le .jpg et ce qui suit (en cherchant sa position)
					# on prend la fin => 618/719/212, si cela commence par un 0 on l'enlève et on enlève ensuite les / pour obtenir
					# 618/719/212 => 618719212
					# cela nous permet de retrouver l'id et donc de pouvoir affecter
					# de plus on transforme le thumb en large (la requête xpath se chargant de récupérer les thumbs )
					# imageId=item[:item.find('.jpg')][-16:-4].replace('/','').strip('0')
					imageId=item.split('auction/')[1].split('_')[0].replace('/','').lstrip('0')
					# print(imageId)
					# print("po")
					# while imageId[0] == '0':
					# 	imageId=imageId[1:]
					listeVentestemp[imageId]["images"].append(item[:item.find('?v=')].replace('img_thumb','img_large'))

				for id in listeVentestemp:
					listeVentes.append(vente(id,listeVentestemp[id]))
			else:
				print('Problème lecture {0} . Code retour : {1}'.format(page,r.status_code))

			# on ne veut pas les objets de cpaphil, on repasse donc les ventes et on supprime les lignes en question
			for item in listeVentes:
				if item.vendeur!='cpaphil':
					listeVentesNettoyées.append(item)
		return listeVentesNettoyées

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
		self.prix=dict['prix'].replace(",",".")
		#self.url=url
		self.vendeur=dict['vendeur']
		self.libellé=dict['libellé']
		self.images={}
		for img in dict['images']:
			numImage=img[:img.find('.jpg')][-3:]
			# on récupère l'url
			try:
				self.images[numImage]['url']=img
			except:
				self.images[numImage]={}
				self.images[numImage]['url']=img
			# on calcule le libellé pour le téléchargement
			self.images[numImage]['nomImage']='{0}_{1}_prix:{2}_{3}_{4}.jpg'.format(self.id,self.vendeur,self.prix,self.libellé,numImage)

		self.nbImages=len(self.images)
		self.listeimages=self.get_listeimages()

	def info(self):
		print("\nid : {0}".format(self.id))
		print("Libellé : {0}".format(self.libellé))
		print("vendeur : {0}".format(self.vendeur))
		print("prix : {0}".format(self.prix))
		print("Nb images : {0}".format(self.nbImages))
		# print("images : {0}".format(self.images))
		for lesimages in self.images:
			print('\turl : {0}'.format(self.images[lesimages]['url']))
			print('\tnom image : {0}'.format(self.images[lesimages]['nomImage']))
			# print('nom image :{0}'.format(self.images[lesimages]['nomImages']))

	def get_listeimages(self):
		listeurl=[]
		listenoms=[]
		listeimages=[]
		for lesimages in self.images:
			# print('b : {0}'.format(self.images[lesimages]['url']))
			listeimages.append([self.images[lesimages]['url'],self.images[lesimages]['nomImage']])
			# listenoms.append(self.images[lesimages]['nomImage'])
			# listeimages.append([listeurl,listenoms])
		return listeimages

	def download_images_multi_cpu(self,rechercheimage):
		# on crée le dir si il n'existe pas
		cpus = multiprocessing.cpu_count()
		max_pool_size=4
		# pool= multiprocessing.Pool(cpus if cpus < max_pool_size else max_pool_size)
		pool=multiprocessing.Pool(100)

		download_dir=rechercheimage.download_dir
		dirAcreer = Path(download_dir)
		if not dirAcreer.exists():
			dirAcreer.mkdir(parents=True, exist_ok=True)
		for lesimages in self.images:
			url=self.images[lesimages]['url']
			dest='{1}/{2}'.format(self.images[lesimages]['url'],download_dir,self.images[lesimages]['nomImage'])
			if not os.path.isfile(dest):
				try:
					# wget.download(url,dest)
					pool.apply_async(run_process, args=(url, dest, ))
				except:
					print('Erreur sur {0}'.format(url))

		pool.close()
		pool.join()
		print("finish")

def download_multicpu(liste,rechercheimage):
	# on crée le dir si il n'existe pas
	cpus = multiprocessing.cpu_count()
	max_pool_size=20
	pool= multiprocessing.Pool(cpus if cpus < max_pool_size else max_pool_size)

	download_dir=rechercheimage.download_dir
	print(download_dir)
	dirAcreer = Path(download_dir)
	if not dirAcreer.exists():
		dirAcreer.mkdir(parents=True, exist_ok=True)
	for dl in liste:
		url=dl[0][0]
		dest='{0}/{1}'.format(download_dir,dl[0][1])
	# if not os.path.isfile(dest):
			# try:
				# wget.download(url,dest)
		pool.apply_async(run_process, args=(url, dest, ))
			# except:
			# 	print('Erreur sur {0}'.format(url))

	pool.close()
	pool.join()
	print("finish")

def download_multithread(liste,rechercheimage):
	# on crée le dir si il n'existe pas
	maxthread = 60

	download_dir=rechercheimage.download_dir
	print(download_dir)
	dirAcreer = Path(download_dir)
	if not dirAcreer.exists():
		dirAcreer.mkdir(parents=True, exist_ok=True)
	for dl in liste:
		for dl1 in dl:
			while threading.activeCount() > maxthread:
				print('threading.activeCount={0}'.format(threading.activeCount()))
				time.sleep(1)
			try :
				url=dl1[0]
				dest='{0}/{1}'.format(download_dir,dl1[1])
				t = threading.Thread(target=run_process, args=(url, dest))
				t.start()
			except:
				print('problème avec {0}'.format(dl))

	time.sleep(5)
	print('\nthreading.activeCount={0}'.format(threading.activeCount()))
	print('add all pic to download list..')
	cthread = threading.current_thread()
	for t in threading.enumerate():
		if t != cthread:
			pass #t.terminate()
	print('bye..')

	# if not os.path.isfile(dest):
			# try:
	wget.download(url,dest)
# def recherche_multithread(section,term):
# 	# on crée le dir si il n'existe pas
# 	maxthread = 60
#
# 	for fini in (True,False)
# 		t = threading.Thread(target=recherche, args=(section, term, True))
# 		t.start()
#
# 	time.sleep(5)
# 	print('threading.activeCount={0}'.format(threading.activeCount()))
# 	print('add all pic to download list..')
# 	cthread = threading.current_thread()
# 	for t in threading.enumerate():
# 		if t != cthread:
# 			pass #t.terminate()
# 	print('bye..')
#
# 	# if not os.path.isfile(dest):
# 			# try:
# 				# wget.download(url,dest)


if __name__ == "__main__":

	homedir='/home/whinpo/Philatélie/pompage_sites/Delcampe2'
	main(sys.argv[1:])

	#url='https://www.delcampe.net/fr/collections/search?categories%5B%5D=674&search_mode=all&excluded_terms=&is_searchable_in_descriptions=0&is_searchable_in_translations=0&term=1900+&show_type=all&display_ongoing=ongoing&started_days=&started_hours=&ended_hours=&display_only=&min_price=&max_price=&currency=all&seller_localisation=&view=thumbs&order=&country=&size=%s' s ($size)
	print(commande)

	print(section)

	# rechercheEnCours=recherche(section,term,False)
	liste_dl=[]

	liste_dl=[]

	for closed in (False, True):
		liste_dl=[]

		rechercheventes=recherche(section,term,closed)
		for lesventes in rechercheventes.ventes:
			# pp.pprint(lesventes.listeimages)
			# print('a : {0}'.format(lesventes.listeimages))
			liste_dl.append(lesventes.listeimages)
		for dl in liste_dl:
			print(dl)
			print(len(dl))
			for dl1 in dl:
				try:
					print('url : {0}'.format(dl1[0]))
					print('nom : {0}\n'.format(dl1[1]))
				except:
					print('pb sur {0}'.format(dl1))
		pp = pprint.PrettyPrinter(indent=4)
		# pp.pprint(liste_dl)
		# print(liste_dl)
		download_multithread(liste_dl,rechercheventes)
