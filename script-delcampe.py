#!/usr/bin/env python3 
import sys, getopt
from requests_html import HTMLSession
session = HTMLSession()

def usage():
	print('script-delcame.py -c <collection> -s <section> -t <terme de recherche> <-n maxscreens>  [- si vendu],["collection=","section="]')
	
def main(argv):
	global commande
	global collection 
	global optionC
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
		opts, args = getopt.getopt(argv,"c:s:t:m:hv",["collection=","section=","term=","maxscreens="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt in ("-c", "--collection"):
			collection=arg
			optionC='-c {0}'.format(collection)
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
						

	# on contrôle que -c et -s ont bien été remplis !
	if not collection:
		print('Param -c obligatoire')
		usage()
		sys.exit(2)
		
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

	commande='script-delcampe.py {0} {1} {2} {3} {4}'.format(optionC,optionS,optionT,optionM,optionV)

		
def generateSearchURL(collection,section,term,vendu):
	global url
	# nb de réponses par page sur Delcampe
	size='480'
		
	# si on a un critère de recherche
	termURL=''
	if term:
		termURL='&term={0}'.format(term)
	
	# on veut voir les ventes cloturées
	displayongoing=''
	if vendu:
		displayongoing='&display_ongoing=closed'
		
	url='https://www.delcampe.net/fr/collections/{0}/{1}/search?size={2}{3}{4}'.format(collection,section,size,termURL,displayongoing)
	return url

if __name__ == "__main__":


	main(sys.argv[1:])
	
	#url='https://www.delcampe.net/fr/collections/search?categories%5B%5D=674&search_mode=all&excluded_terms=&is_searchable_in_descriptions=0&is_searchable_in_translations=0&term=1900+&show_type=all&display_ongoing=ongoing&started_days=&started_hours=&ended_hours=&display_only=&min_price=&max_price=&currency=all&seller_localisation=&view=thumbs&order=&country=&size=%s' s ($size)
	print(commande)
	
	# on génère la page de recherche principale
	url=generateSearchURL(collection,section,term,vendu)
	print(url)
	
	# on se connecte sur la page
	r = session.get(url)
	
	# liste des ventes
	#print(r.html.xpath('//*[@id]/div/div[1]/div/a[@class="item-link"]/@href'))

	# liste des pages
	listepages=r.html.xpath('//*[@class="pag-number"]/text()')
	nbpages=listepages[-1]
	
	print(nbpages)








