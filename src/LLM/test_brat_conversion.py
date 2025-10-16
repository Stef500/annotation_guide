#!/usr/bin/env python3
"""
Script de test pour la conversion LangExtract vers BRAT
Teste la conversion avec des données d'exemple et valide les résultats
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from loguru import logger

# Ajout du répertoire parent pour les imports
sys.path.append(str(Path(__file__).parent))

from langextract_to_brat import LangExtractToBratConverter


def create_test_jsonl_data() -> str:
    """
    Crée des données JSONL de test similaires à la sortie de LangExtract

    Returns:
        Chemin vers le fichier JSONL temporaire
    """
    test_data = [
        {
            "text": "Patient admis pour bactériémie à S. aureus résistant à la méthicilline. Point de départ sur cathéter central. Compliquée par embole septique pulmonaire. Absence d'argument pour endocardite.",
            "extractions": [
                {
                    "extraction_class": "bacteriemie",
                    "extraction_text": "bactériémie",
                    "char_interval": {"start_pos": 17, "end_pos": 28},
                    "attributes": {
                        "type": "infection_sanguine",
                        "contexte": "admission"
                    }
                },
                {
                    "extraction_class": "bacterie",
                    "extraction_text": "S. aureus",
                    "char_interval": {"start_pos": 31, "end_pos": 40},
                    "attributes": {
                        "nom_complet": "Staphylococcus aureus",
                        "type": "cocci_gram_positif",
                        "variante": "abrégé"
                    }
                },
                {
                    "extraction_class": "resistance",
                    "extraction_text": "résistant à la méthicilline",
                    "char_interval": {"start_pos": 41, "end_pos": 68},
                    "attributes": {
                        "type": "SARM",
                        "antibiotique": "méthicilline",
                        "profil": "résistant"
                    }
                },
                {
                    "extraction_class": "site_primaire",
                    "extraction_text": "cathéter central",
                    "char_interval": {"start_pos": 86, "end_pos": 102},
                    "attributes": {
                        "type": "cathéter",
                        "localisation": "central",
                        "certitude": "probable"
                    }
                },
                {
                    "extraction_class": "site_secondaire",
                    "extraction_text": "embole septique pulmonaire",
                    "char_interval": {"start_pos": 117, "end_pos": 143},
                    "attributes": {
                        "type": "complication",
                        "localisation": "poumon",
                        "mécanisme": "embole_septique"
                    }
                },
                {
                    "extraction_class": "negation",
                    "extraction_text": "Absence d'argument",
                    "char_interval": {"start_pos": 145, "end_pos": 163},
                    "attributes": {
                        "type": "négation_médicale",
                        "concept_nié": "endocardite",
                        "force": "forte"
                    }
                },
                {
                    "extraction_class": "infection",
                    "extraction_text": "endocardite",
                    "char_interval": {"start_pos": 169, "end_pos": 180},
                    "attributes": {
                        "type": "cardio_vasc",
                        "statut": "écartée",
                        "relation_bacteriemie": "complication_recherchée"
                    }
                }
            ]
        },
        {
            "text": "E. coli BLSE isolé dans les urines. Les hémocultures ne révèlent pas de bactériémie associée. Abcès rénal documenté par scanner.",
            "extractions": [
                {
                    "extraction_class": "bacterie",
                    "extraction_text": "E. coli",
                    "char_interval": {"start_pos": 0, "end_pos": 7},
                    "attributes": {
                        "nom_complet": "Escherichia coli",
                        "type": "entérobactérie",
                        "variante": "abrégé"
                    }
                },
                {
                    "extraction_class": "resistance",
                    "extraction_text": "BLSE",
                    "char_interval": {"start_pos": 8, "end_pos": 12},
                    "attributes": {
                        "type": "béta_lactamase_spectre_étendu",
                        "mécanisme": "enzymatique",
                        "profil": "résistant_béta_lactamines"
                    }
                },
                {
                    "extraction_class": "site_primaire",
                    "extraction_text": "urines",
                    "char_interval": {"start_pos": 29, "end_pos": 35},
                    "attributes": {
                        "type": "urines",
                        "prélèvement": "ECBU",
                        "rôle": "point_de_départ"
                    }
                },
                {
                    "extraction_class": "negation",
                    "extraction_text": "ne révèlent pas",
                    "char_interval": {"start_pos": 54, "end_pos": 69},
                    "attributes": {
                        "type": "négation_résultat",
                        "concept_nié": "bactériémie",
                        "force": "forte"
                    }
                },
                {
                    "extraction_class": "bacteriemie",
                    "extraction_text": "bactériémie associée",
                    "char_interval": {"start_pos": 73, "end_pos": 93},
                    "attributes": {
                        "type": "complication_recherchée",
                        "statut": "absente",
                        "méthode": "hémocultures"
                    }
                },
                {
                    "extraction_class": "infection",
                    "extraction_text": "Abcès rénal",
                    "char_interval": {"start_pos": 95, "end_pos": 106},
                    "attributes": {
                        "type": "urines",
                        "forme": "abcès",
                        "localisation": "rein",
                        "diagnostic": "scanner"
                    }
                }
            ]
        }
    ]

    # Création d'un fichier temporaire
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8')

    for doc in test_data:
        json.dump(doc, temp_file, ensure_ascii=False)
        temp_file.write('\n')

    temp_file.close()
    return temp_file.name


def validate_brat_files(output_dir: str) -> bool:
    """
    Valide les fichiers BRAT générés

    Args:
        output_dir: Répertoire contenant les fichiers BRAT

    Returns:
        True si la validation réussit
    """
    success = True

    # Vérification des fichiers de configuration
    annotation_conf = os.path.join(output_dir, 'annotation.conf')
    visual_conf = os.path.join(output_dir, 'visual.conf')

    if not os.path.exists(annotation_conf):
        logger.error("Fichier annotation.conf manquant")
        success = False
    else:
        logger.success("annotation.conf présent")

    if not os.path.exists(visual_conf):
        logger.error("Fichier visual.conf manquant")
        success = False
    else:
        logger.success("visual.conf présent")

    # Vérification des paires .txt/.ann
    txt_files = list(Path(output_dir).glob('*.txt'))
    ann_files = list(Path(output_dir).glob('*.ann'))

    logger.info(f"Fichiers .txt trouvés : {len(txt_files)}")
    logger.info(f"Fichiers .ann trouvés : {len(ann_files)}")

    if len(txt_files) != len(ann_files):
        logger.warning("Nombre inégal de fichiers .txt et .ann")
        success = False

    # Validation du contenu des fichiers
    for txt_file in txt_files:
        ann_file = txt_file.with_suffix('.ann')

        if not ann_file.exists():
            logger.error(f"Fichier .ann manquant pour {txt_file.name}")
            success = False
            continue

        # Vérification du contenu .txt
        with open(txt_file, 'r', encoding='utf-8') as f:
            txt_content = f.read()
            if not txt_content.strip():
                logger.warning(f"Fichier .txt vide : {txt_file.name}")

        # Vérification du contenu .ann
        with open(ann_file, 'r', encoding='utf-8') as f:
            ann_content = f.read()
            if not ann_content.strip():
                logger.warning(f"Fichier .ann vide : {ann_file.name}")
                continue

            # Validation du format des annotations
            valid_ann = validate_ann_format(ann_content, txt_content, txt_file.name)
            if not valid_ann:
                success = False

    return success


def validate_ann_format(ann_content: str, txt_content: str, filename: str) -> bool:
    """
    Valide le format des annotations BRAT

    Args:
        ann_content: Contenu du fichier .ann
        txt_content: Contenu du fichier .txt
        filename: Nom du fichier pour les messages d'erreur

    Returns:
        True si le format est valide
    """
    success = True
    entity_ids = set()
    txt_bytes = txt_content.encode('utf-8')

    for line_num, line in enumerate(ann_content.split('\n'), 1):
        line = line.strip()
        if not line:
            continue

        # Validation des entités (Txx)
        if line.startswith('T'):
            parts = line.split('\t')
            if len(parts) != 3:
                logger.error(f"{filename}:{line_num} - Format d'entité invalide: {line}")
                success = False
                continue

            entity_id, type_and_pos, entity_text = parts

            # Validation de l'ID d'entité
            if not entity_id.startswith('T') or not entity_id[1:].isdigit():
                logger.error(f"{filename}:{line_num} - ID d'entité invalide: {entity_id}")
                success = False
                continue

            entity_ids.add(entity_id)

            # Validation du type et positions
            type_pos_parts = type_and_pos.split(' ', 1)
            if len(type_pos_parts) != 2:
                logger.error(f"{filename}:{line_num} - Format type/position invalide: {type_and_pos}")
                success = False
                continue

            entity_type, positions = type_pos_parts

            # Validation des positions
            try:
                for pos_range in positions.split(';'):
                    start, end = map(int, pos_range.split())
                    if start >= end or start < 0 or end > len(txt_bytes):
                        logger.warning(f"{filename}:{line_num} - Position suspecte: {start}-{end}")

                    # Vérification de correspondance du texte
                    segment = txt_bytes[start:end]
                    try:
                        actual_text = segment.decode('utf-8')
                    except UnicodeDecodeError:
                        logger.warning(
                            f"{filename}:{line_num} - Impossible de décoder le segment UTF-8"
                        )
                        actual_text = ""

                    if actual_text.strip() != entity_text.strip():
                        logger.warning(f"{filename}:{line_num} - Texte ne correspond pas:")
                        logger.warning(f"    Attendu: '{entity_text}'")
                        logger.warning(f"    Trouvé:  '{actual_text}'")

            except (ValueError, IndexError) as e:
                logger.error(f"{filename}:{line_num} - Erreur de position: {e}")
                success = False

        # Validation des attributs (Axx)
        elif line.startswith('A'):
            parts = line.split('\t')
            if len(parts) != 2:
                logger.error(f"{filename}:{line_num} - Format d'attribut invalide: {line}")
                success = False
                continue

            attr_id, attr_def = parts
            attr_parts = attr_def.split(' ', 2)

            if len(attr_parts) < 2:
                logger.error(f"{filename}:{line_num} - Définition d'attribut invalide: {attr_def}")
                success = False
                continue

            attr_name, target_entity = attr_parts[0], attr_parts[1]

            # Validation de la référence d'entité
            if target_entity not in entity_ids:
                logger.warning(f"{filename}:{line_num} - Référence d'entité non trouvée: {target_entity}")

    return success


def run_conversion_test():
    """Exécute le test complet de conversion"""
    logger.info("TEST DE CONVERSION LANGEXTRACT → BRAT")
    logger.info("=" * 50)

    # Création des données de test
    logger.info("1. Création des données de test...")
    test_jsonl = create_test_jsonl_data()
    logger.success(f"Fichier de test créé : {test_jsonl}")

    # Création du répertoire de sortie temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "brat_output")

        try:
            # Conversion
            logger.info("2. Conversion vers BRAT...")
            converter = LangExtractToBratConverter()
            converter.convert_jsonl_to_brat(test_jsonl, output_dir, "test")

            # Validation
            logger.info("3. Validation des fichiers BRAT...")
            validation_success = validate_brat_files(output_dir)

            # Affichage des résultats
            logger.info("4. Aperçu des fichiers générés...")
            files = list(Path(output_dir).iterdir())
            for file in sorted(files):
                size = file.stat().st_size if file.is_file() else 0
                logger.info(f"   {file.name} ({size} bytes)")

            # Test d'un fichier .ann en détail
            ann_files = list(Path(output_dir).glob('*.ann'))
            if ann_files:
                logger.info(f"5. Contenu de {ann_files[0].name} :")
                with open(ann_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    for i, line in enumerate(content.split('\n')[:10], 1):  # Premiers 10 lignes
                        if line.strip():
                            logger.info(f"   {i}: {line}")

            # Résultat final
            if validation_success:
                logger.success("TEST RÉUSSI ! Conversion validée.")
                logger.info(f"Fichiers générés dans : {output_dir}")
            else:
                logger.warning("TEST PARTIEL. Quelques avertissements détectés.")

        except Exception as e:
            logger.error(f"ERREUR PENDANT LE TEST : {e}")
            return False

        finally:
            # Nettoyage du fichier temporaire
            os.unlink(test_jsonl)

    return validation_success


def test_with_real_data():
    """Test avec des données réelles si disponibles"""
    real_data_file = "extraction_comptes_rendus.jsonl"

    if os.path.exists(real_data_file):
        logger.info("TEST AVEC DONNÉES RÉELLES")
        logger.info("=" * 40)

        output_dir = "brat_output_real"

        try:
            converter = LangExtractToBratConverter()
            converter.convert_jsonl_to_brat(real_data_file, output_dir, "real")

            logger.success("Conversion réelle terminée !")
            logger.info(f"Résultats dans : {output_dir}")
            return True

        except Exception as e:
            logger.error(f"Erreur conversion réelle : {e}")
            return False
    else:
        logger.info(f"Pas de données réelles trouvées ({real_data_file})")
        logger.info("Exécutez d'abord extraction_comptes_rendus.py")
        return True  # Pas d'erreur, juste pas de fichier


def main():
    """Fonction principale"""
    success = True

    # Test avec données simulées
    if not run_conversion_test():
        success = False

    # Test avec données réelles si disponibles
    if not test_with_real_data():
        success = False

    logger.info("RÉSUMÉ DES TESTS")
    logger.info("=" * 30)

    if success:
        logger.success("Tous les tests sont passés avec succès !")
        logger.info("UTILISATION :")
        logger.info("   python langextract_to_brat.py input.jsonl output_dir/")
    else:
        logger.warning("Certains tests ont échoué. Vérifiez les messages ci-dessus.")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
