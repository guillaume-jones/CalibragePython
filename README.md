# CalibragePython

Répertoire de stage à l'été 2021 sous la direction de Lama Séoud.
Actuellement, le répertoire permet de calibrer une caméra RGB avec calibrate.py, et d'appliquer le calibrage sur une autre image avec undistort.py.

## Installation

1. Installer [miniconda](https://docs.conda.io/en/latest/miniconda.html).
2. Cloner le répertoire.
3. Créer l'environnement avec la commande suivante (une fois) : 
```bash
conda env create -f environment.yml
```
4. Utiliser la commande suivante pour activer l'environnement à chaque fois :
```bash
conda activate stage2021 
```

## Utilisation

Si vous n'avez pas de checkerboard, imprimez-en un avec le fichier Resources/Checkerboard.pdf.
Pour calibrer une caméra, simplement activer l'environnement et effectuer :
```
python calibrate.py
```
Ensuite, déplacer le checkerboard afin de couvrir toute l'image de la caméra de quadrilatères verts.
Lorsque le compte d'image à prendre atteint 0, le logiciel peut demander de prendre des captures à nouveau.
Ceci signifie qu'il a rejeté des captures trop floues/imprécises, et il faut simplement en reprendre.
Les recommendations suivantes sont à suivre pour un calibrage optimal : (tirés de [ce lien](https://stackoverflow.com/questions/12794876/how-to-verify-the-correctness-of-calibration-of-a-webcam/12821056#12821056)):
1. Avoir un bon éclairage
2. Bien fixer la caméra
3. Placer le checkerboard à un angle de la caméra (pas de face directement)
4. Couvrir toute l'image et tout le volume de l'espace à calibrer
5. Éviter le motion blur dans les images
6. S'assurer que le checkerboard est le plus rigide possible

Le calibrage est stocké dans le fichier `calibrationFile.json`.

Une fois le calibrage effectué, utiliser la commande suivante pour appliquer le calibrage à la caméra actuelle :
```
python undistort.py
```
