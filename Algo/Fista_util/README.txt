Applic_Fista
== Description ==
Applic_Fista.py can be used for performing superresolution on FTICR or Orbitrap data or for testing superresolutioon on shorted Fid. 
Stable version: 0.1

== Installation ==
For running the code you have to install Canopy https://www.enthought.com/products/canopy/ 
or Anaconda https://store.continuum.io/cshop/anaconda/
In the config file "Applic_Fista.mscf" enter the path to the main package "draft_Fista".
i.e : npk_dir = path to draft_Fista
"draft_Fista" contains the directory Fista_applic, util, v1 and other dependencies. 
In /draft_Fista/Applic_Fista, copy the file "Applic_Fista_eg.mscf" and change its name to "Applic_Fista.mscf"  (no "_eg").


== Configuration ==
Before using Fista you need to change the config file "Applic_Fista.mscf". 
Four sections need to be changed : config, data, fista and store.
The first one is for specifying the path to the main package (see here above).
The following ones are :
= data =
	It is related to the data you want to treat. It is possible to treat only one file.
	In that case the "directory_to_treat" is empty i.e : directory_to_treat = 
	and "file_to_treat" is given a path to the file to treat
	file_to_treat = path to file 
	The name of the path are written without commas.
	In the case you want to launch Fista on a directory, simply give
	the path of the directory to the parameter "directory_to_treat". 
	directory_to_treat = path to the directory to Fistaed. 
= fista =
	This section is used to parametrize the experiment for Fista.
	div_by : is the parameter for dividing the Fid if you want to examinate how Fista retrieve the
		signal from shorter transients. If you want to perform superresolution on native Fid, use div_by = 1
	first_point : this is the first point of in the frame of the original dataset when the user
		want to apply Fista on a chunk of the original Fid. 
		When performing superresolution on the original dataset, use first_point = 0
	do_fista : specify if the user want to apply Fista or not.. True or False
		By default it is True
	surresol : parameter of superresolution for Fista. 
		The user gives an integer. 
	zerofill_ref : Zerofilling for the FOurier Transform of the reference dataset. 
	noise_correct : parameter permitting to the user to change the noise level estimate in Fista. 
		It divides the noise level estimated in Fista. 
		noise_correct = 2 will lower by a factor 2 the estimated noise level and it will be possible
		 to see peaks sometimes hidden very near from the estimated noise.
	mp : parameter for multiprocessing. True or False. 
	show_cut : For visualizing if the cut of the FId is correct select this parameter to True. 
		By default its value is False. 
== Running ==
To run the program once the installation and configuration achieved, in Canopy browse to the file /draft_Fista/Fista_applic/Applic_Fista.py and execute. 
In Anaconda launch Python from /bin/python2.7 i.e write : Anaconda/bin/python2.7  /draft_Fista/Fista_applic/Applic_Fista.py
	
== Changelog ==

= 0.1 =
* added the possibility to change the estimated noise level, parameter noise_correct in the config file. 
* displaced the switch for multiprocessing in the config file. 
* added a switch for showing or not where the Fid is cut. 
* saving the config file with the results.
* m/z transformation according to the range of the orbitrap dataset.


