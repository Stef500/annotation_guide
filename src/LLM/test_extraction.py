#!/usr/bin/env python3
"""
Script de test et de configuration pour l'extraction de comptes rendus
Teste le script principal avec des exemples simples avant traitement complet
"""

import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Ajout du répertoire parent pour importer le module principal
sys.path.append(str(Path(__file__).parent))

from extraction_comptes_rendus import ExtractionComptesRendus


def tester_configuration():
    """Teste la configuration de base"""
    logger.info("Test de configuration...")

    # Vérification de la clé API OpenAI
    api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('LANGEXTRACT_API_KEY')
    if not api_key:
        logger.warning("Variable OPENAI_API_KEY non définie")
        logger.info("Définissez votre clé API dans le fichier .env :")
        logger.info("OPENAI_API_KEY='votre-cle-openai'")
        return False

    logger.success("Clé API configurée")

    # Test d'initialisation
    try:
        extracteur = ExtractionComptesRendus()
        logger.success("Extracteur initialisé avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur d'initialisation : {e}")
        return False


def tester_extraction_simple():
    """Teste l'extraction sur un texte simple"""
    logger.info("Test d'extraction simple...")

    # Texte de test basé sur la terminologie médicale des bactériémies
    texte_test = """
    Patient admis aux urgences pour septicémie à S. aureus.
    Hémocultures positives à Staphylococcus aureus résistant à la méthicilline.
    Point de départ probablement sur cathéter central.
    Compliquée par un embole septique pulmonaire.
    Absence d'argument en faveur d'une endocardite.
    E. coli BLSE isolé dans les urines sans bactériémie associée.
    """

    try:
        extracteur = ExtractionComptesRendus()

        # Création d'un fichier temporaire
        fichier_temp = "test_temp.txt"
        with open(fichier_temp, 'w', encoding='utf-8') as f:
            f.write(texte_test)

        # Extraction
        resultat = extracteur.extraire_fichier(fichier_temp, passes=1)

        # Affichage des résultats
        logger.success(f"Extraction réussie : {len(resultat.extractions)} entités trouvées")

        logger.info("Entités extraites :")
        for i, extraction in enumerate(resultat.extractions, 1):
            logger.info(f"{i}. {extraction.extraction_class}: '{extraction.extraction_text}'")
            if extraction.attributes:
                for cle, valeur in extraction.attributes.items():
                    logger.info(f"   - {cle}: {valeur}")

        # Nettoyage
        os.remove(fichier_temp)

        return True

    except Exception as e:
        logger.error(f"Erreur lors du test d'extraction : {e}")
        if os.path.exists(fichier_temp):
            os.remove(fichier_temp)
        return False


def configurer_environnement():
    """Guide de configuration de l'environnement"""
    logger.info("GUIDE DE CONFIGURATION")
    logger.info("=" * 50)

    logger.info("1. Installation des dépendances :")
    logger.info("   uv add langextract python-dotenv loguru")
    logger.info("   # ou avec pip :")
    logger.info("   pip install langextract python-dotenv loguru")

    logger.info("2. Configuration de la clé API :")
    logger.info("   # Option 1: Fichier .env (recommandé)")
    logger.info("   cp .env.example .env")
    logger.info("   # Puis éditez .env et ajoutez votre clé OpenAI")
    logger.info("   # Option 2: Variable d'environnement")
    logger.info("   export OPENAI_API_KEY='votre-cle-openai'")

    logger.info("3. Obtenir une clé API OpenAI :")
    logger.info("   • OpenAI (GPT-4o-mini) : https://platform.openai.com/api-keys")
    logger.info("   • Créez un compte et générez une nouvelle clé API")

    logger.info("4. Test de configuration :")
    logger.info("   python test_extraction.py")


def afficher_aide():
    """Affiche l'aide d'utilisation"""
    logger.info("AIDE D'UTILISATION")
    logger.info("=" * 50)

    logger.info("Commandes disponibles :")
    print("  python test_extraction.py              # Test complet")
    print("  python test_extraction.py config       # Guide de configuration")
    print("  python test_extraction.py test         # Test simple")
    print("  python test_extraction.py help         # Cette aide")

    print("\nUtilisation du script principal :")
    print("  python extraction_comptes_rendus.py    # Extraction complète")

    print("\nStructure des fichiers :")
    print("  📂 src/LLM/")
    print("  ├── 📄 extraction_comptes_rendus.py    # Script principal")
    print("  ├── 📄 test_extraction.py              # Tests et configuration")
    print("  └── 📄 README_extraction.md            # Documentation")


def executer_tests_complets():
    """Exécute tous les tests"""
    logger.info("TESTS COMPLETS D'EXTRACTION")
    print("=" * 50)

    # Test 1: Configuration
    if not tester_configuration():
        logger.error("Échec du test de configuration")
        configurer_environnement()
        return False

    # Test 2: Extraction simple
    if not tester_extraction_simple():
        logger.error("Échec du test d'extraction")
        return False

    logger.success("Tous les tests sont passés avec succès !")
    logger.info("Vous pouvez maintenant utiliser :")
    print("   python extraction_comptes_rendus.py")

    return True


def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        commande = sys.argv[1].lower()

        if commande == "config":
            configurer_environnement()
        elif commande == "test":
            if tester_configuration():
                tester_extraction_simple()
        elif commande == "help":
            afficher_aide()
        else:
            logger.error(f"Commande inconnue : {commande}")
            afficher_aide()
    else:
        # Exécution complète par défaut
        executer_tests_complets()


if __name__ == "__main__":
    main()