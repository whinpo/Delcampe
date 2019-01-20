#!/usr/bin/env python3
import sys, getopt
import logging
import os
import pprint
from pathlib import Path
import requests
import wget
import threading
import time
import re
import bs4 as BeautifulSoup


def run_process(url, output_path):
	# print('download {0} vers {1}'.format(url,output_path))
	if not os.path.isfile(output_path):
		try:
			wget.download(url, out=output_path)
		except:
			print('\nproblème d/l {0}'.format(url))

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
		print('pages : {0}'.format(self.pages))
		print('nb images : {0}'.format(self.nbImages))
		print('nb Ventes : {0}'.format(self.nbVentes))
		print('Download Dir : {0}'.format(self.download_dir))


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
		url='{0}/{1}/search?view=gallery&order=sale_start_datetime&country=NET&view=thumbs&size={2}{3}{4}'.format(self.urlDelcampeCollections,self.section,self.size,termURL,displayongoing)
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
		r = requests.get(self.searchURL)
		soup=BeautifulSoup.BeautifulSoup(r.text,"lxml")
		# on parse le résultat avec beautifulSoup
		# on contrôle que la connexion est OK
		if r.status_code == 200:
			print('Lecture URL : OK')

			# on recherche les a de classe pag-number, si on ne trouve pas => 1 page seulement
			try:
				nbpages=soup.find_all('a',class_='pag-number')[-1].get_text()
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
		# liste des vendeurs non voulus
		vendeursNonVoulus=['cpaphil']

		for page in self.pages:
			print('Récupération de la liste des ventes de la page {0}/{1}'.format(numpage,self.nbPages))
			# on se connecte sur la page
			r = requests.get(self.searchURL)
			# on contrôle que la connexion est OK
			if r.status_code == 200:
				print('Lecture URL {0} : OK'.format(page))

				print('Status : {0}'.format(r.status_code))
				print('Analyse de la page en cours {0}'.format(page))
				numpage=numpage+1

				# on crée une liste listeVentes qui va contenir un nested dictionnary
				listeVentes=[]

				# commande BeautifulSoup pour récupérer l'ensemble des ventes (id avec valeur item-999999)
				soup=BeautifulSoup.BeautifulSoup(r.text,"lxml")
				listeventes=soup.find_all(id=re.compile('item-\d'))
				nbVentesPage=len(listeventes)
				i=1
				for vente_item in listeventes:
					# print('On traite : {0} - ({1}/{2})'.format(vente_item['id'],i,nbVentesPage))
					i+=1
					venteDef={}
					id=vente_item['id'].split('-')[1]
					# on regarde si il y a bien une image
					try:
						test=vente_item.find('div',class_='image-content').a.img
						# si oui on regarde si vendeur non voulu ou pas
						vendeur=vente_item.find('div',class_='option-content').a['title']
						if vendeur not in vendeursNonVoulus:
							# print(vendeur)
							# on a des images et un vendeur voulu => on crée la vente
							prix=vente_item.find('div',class_='item-price').get_text().strip()[:-2].replace(',','.')
							venteDef['id']=id
							venteDef['vendeur']=vendeur
							venteDef['prix']=prix
							venteDef['listeImages']=[]

							for listeimages in vente_item.find_all('div',class_='image-content'):
								imageDef=[]
								imagebrute=listeimages.a.img['data-lazy']
								# on supprimer le ?v=2 de la fin et on remplace thumb par large
								image=imagebrute.split('?')[0].replace('img_thumb','img_large')
								# on contruit le libellé : id_vendeur_prix:prix_libellélisible_001.jpg par exemple
								# pour le _001.jpg on utilise rsplit pour prendre _001.jpg?v=2 et on coupe ensuite
								libelle='{0}_{1}_prix:{2}_{3}_{4}'.format(id,vendeur,prix,urlify(listeimages.a.img['alt']),imagebrute.rsplit('_',1)[1].split('?')[0])
								# print(image)
								# print(libelle)
								imageDef=[image,libelle]
								venteDef['listeImages'].append(imageDef)

							# print(venteDef)
							listeVentes.append(vente(venteDef))

						else:
							print('{0}-{1}-VENDEUR pas Voulu'.format(id,vendeur))


					except:
						print('{0} - ERREUR Aucune image'.format(id))

			else:
				print('Problème lecture {0} . Code retour : {1}'.format(page,r.status_code))
		# for lesventes in listeVentes:
		# 	print("\n")
		# 	lesventes.get_info()
		return listeVentes

	# retourne les images de la recherche
	# on fait un boucle sur les images de la vente pour avoir tout dans un seul array
	def get_images(self):
		images=[]
		for ventes in self.ventes:
			for ventesimg in ventes.images:
				images.append(ventesimg)
		return images

	def download_images(self):
		liste_dl=[]
		for lesventes in self.ventes:
			liste_dl.append(lesventes.images)
		# for dl in liste_dl:
		# 	# print(dl)
		# 	# print(len(dl))
		# 	for dl1 in dl:
		# 		try:
		# 			print('url : {0}'.format(dl1[0]))
		# 			print('nom : {0}\n'.format(dl1[1]))
		# 		except:
		# 			print('pb sur {0}'.format(dl1))
		# pp = pprint.PrettyPrinter(indent=4)
		download_multithread(liste_dl,self)

class vente:
	def __init__(self,dict):
		self.id=dict['id']
		self.prix=dict['prix']
		self.vendeur=dict['vendeur']
		self.images=dict['listeImages']
		self.nbImages=len(self.images)

	def get_info(self):
		print("id : {0}".format(self.id))
		print("vendeur : {0}".format(self.vendeur))
		print("prix : {0}".format(self.prix))
		print("Nb images : {0}".format(self.nbImages))
		print("images : {0}".format(self.images))

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
				print('\nthreading.activeCount={0}'.format(threading.activeCount()))
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
		 	# wget.download(url,dest)

def Delcampe_dowload(section,term):
	# on lance la recherche sur les ventes ouvertes et on d/l puis idem pour les fermées
	for closed in (False, True):

		rechercheventes=recherche(section,term,closed)
		rechercheventes.download_images()




if __name__ == "__main__":

	homedir='/home/whinpo/Philatélie/pompage_sites/Delcampe2'
	main(sys.argv[1:])

	#url='https://www.delcampe.net/fr/collections/search?categories%5B%5D=674&search_mode=all&excluded_terms=&is_searchable_in_descriptions=0&is_searchable_in_translations=0&term=1900+&show_type=all&display_ongoing=ongoing&started_days=&started_hours=&ended_hours=&display_only=&min_price=&max_price=&currency=all&seller_localisation=&view=thumbs&order=&country=&size=%s' s ($size)
	print(commande)

	print(section)
	# rechercheventes.ventes
	# rechercheventes.
	Delcampe_dowload(section,term)


	# 	liste_dl=[]

		# rechercheventes=recherche(section,term,closed)
		# for lesventes in rechercheventes.ventes:
		# 	liste_dl.append(lesventes.listeimages)
		# for dl in liste_dl:
		# 	print(dl)
		# 	print(len(dl))
		# 	for dl1 in dl:
		# 		try:
		# 			print('url : {0}'.format(dl1[0]))
		# 			print('nom : {0}\n'.format(dl1[1]))
		# 		except:
		# 			print('pb sur {0}'.format(dl1))
		# pp = pprint.PrettyPrinter(indent=4)
		# download_multithread(liste_dl,rechercheventes)
