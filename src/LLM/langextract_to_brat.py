#!/usr/bin/env python3
"""
Convertisseur LangExtract vers BRAT
Convertit les données JSON extraites par LangExtract au format d'annotation BRAT
"""

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration globale
INPUT_JSONL_FILE = "extraction/extraction_complete.jsonl"  # Fichier JSONL d'entrée
OUTPUT_BRAT_DIR = "BRAT"                           # Répertoire de sortie BRAT
FILE_PREFIX = "doc"                                       # Préfixe pour les noms de fichiers
SHOW_STATS = True                                         # Afficher les statistiques


class LangExtractToBratConverter:
    """Convertisseur des données LangExtract vers le format BRAT"""

    def __init__(self):
        """Initialise le convertisseur"""
        self.entity_types = set()

        # Mapping des types d'entités médicales spécialisées LangExtract vers BRAT
        self.entity_mapping = {
            "bacteriemie": "Bacteriemie",
            "bacterie": "Bacterie",
            "resistance": "Resistance",
            "site_primaire": "Site_Primaire",
            "site_secondaire": "Site_Secondaire",
            "infection": "Infection",
        }

    def load_langextract_data(self, jsonl_file: str) -> List[Dict[str, Any]]:
        """
        Charge les données depuis un fichier JSONL LangExtract

        Args:
            jsonl_file: Chemin vers le fichier JSONL

        Returns:
            Liste des documents avec leurs annotations
        """
        documents = []

        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    doc = json.loads(line)
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    logger.warning(f"Erreur JSON ligne {line_num}: {e}")
                    continue

        logger.info(f"Chargé {len(documents)} documents depuis {jsonl_file}")
        return documents

    def normalize_entity_type(self, entity_type: str) -> str:
        """
        Normalise le nom du type d'entité pour BRAT

        Args:
            entity_type: Type d'entité original

        Returns:
            Type d'entité normalisé compatible BRAT
        """
        # Utilise le mapping si disponible, sinon normalise automatiquement
        if entity_type in self.entity_mapping:
            return self.entity_mapping[entity_type]

        # Normalisation automatique: CamelCase et caractères autorisés
        normalized = re.sub(r'[^a-zA-Z0-9_]', '_', entity_type)
        normalized = ''.join(word.capitalize() for word in normalized.split('_'))
        return normalized

    def validate_span(self, text: str, start: int, end: int, entity_text: str) -> Tuple[int, int, str]:
        """
        Valide et corrige les positions de l'annotation

        Args:
            text: Texte complet du document
            start: Position de début
            end: Position de fin
            entity_text: Texte de l'entité

        Returns:
            Tuple (start_corrigé, end_corrigé, texte_corrigé)
        """
        # Vérification des bornes
        if start < 0:
            start = 0
        if end > len(text):
            end = len(text)
        if start >= end:
            return start, start + 1, text[start:start + 1]

        # Extraction du texte réel
        actual_text = text[start:end]

        # Si le texte correspond exactement
        if actual_text == entity_text:
            return start, end, actual_text

        # Recherche du texte dans un voisinage proche (tolérance aux erreurs mineures)
        search_window = 50
        search_start = max(0, start - search_window)
        search_end = min(len(text), end + search_window)
        search_area = text[search_start:search_end]

        # Recherche exacte
        exact_pos = search_area.find(entity_text)
        if exact_pos != -1:
            corrected_start = search_start + exact_pos
            corrected_end = corrected_start + len(entity_text)
            return corrected_start, corrected_end, entity_text

        # Recherche approximative (ignore la casse et espaces)
        normalized_entity = re.sub(r'\s+', ' ', entity_text.lower().strip())
        normalized_search = re.sub(r'\s+', ' ', search_area.lower())

        approx_pos = normalized_search.find(normalized_entity)
        if approx_pos != -1:
            # Retrouve la position dans le texte original
            corrected_start = search_start + approx_pos
            corrected_end = corrected_start + len(entity_text)
            return corrected_start, corrected_end, text[corrected_start:corrected_end]

        # Si aucune correspondance, utilise les positions originales
        return start, end, actual_text

    def convert_document(self, document: Dict[str, Any], doc_id: str) -> Tuple[str, str]:
        """
        Convertit un document LangExtract en format BRAT

        Args:
            document: Document LangExtract avec text et extractions
            doc_id: Identifiant du document

        Returns:
            Tuple (contenu_.txt, contenu_.ann)
        """
        text = document.get('text', '')
        extractions = document.get('extractions', [])

        # Contenu du fichier .txt
        txt_content = text

        # Génération du fichier .ann
        ann_lines = []
        entity_counter = 1

# Collecte des types pour la configuration BRAT
        for extraction in extractions:
            entity_type = extraction.get('extraction_class', 'Unknown')
            normalized_type = self.normalize_entity_type(entity_type)
            self.entity_types.add(normalized_type)



        # Génération des annotations d'entités
        for extraction in extractions:
            entity_type = extraction.get('extraction_class', 'Unknown')
            normalized_type = self.normalize_entity_type(entity_type)
            entity_text = extraction.get('extraction_text', '')

            # Récupération des positions
            char_interval = extraction.get('char_interval')
            if char_interval:
                start = char_interval.get('start_pos', 0)
                end = char_interval.get('end_pos', len(entity_text))
            else:
                # Recherche automatique de la position si non fournie
                pos = text.find(entity_text)
                if pos != -1:
                    start = pos
                    end = pos + len(entity_text)
                else:
                    # Position par défaut au début
                    start = 0
                    end = len(entity_text)

            # Validation et correction des positions
            start, end, validated_text = self.validate_span(text, start, end, entity_text)

            if not validated_text:
                logger.warning(
                    f"Annotation ignorée (texte introuvable) : '{entity_text}'"
                )
                continue

            if not self._texts_match(entity_text, validated_text):
                candidate_span = self._find_best_span(text, entity_text, start)
                if candidate_span:
                    start, end = candidate_span
                    validated_text = text[start:end]
                else:
                    logger.warning(
                        "Annotation ignorée (décalage non résolu)",
                        extra={
                            "type": normalized_type,
                            "attendu": entity_text,
                            "trouve": validated_text,
                        }
                    )
                    continue

            # Génération de l'annotation d'entité (format BRAT)
            entity_id = f"T{entity_counter}"
            ann_lines.append(
                f"{entity_id}	{normalized_type} {start} {end}	{validated_text}"
            )

            entity_counter += 1

        ann_content = '\n'.join(ann_lines)
        return txt_content, ann_content

    @staticmethod
    def _texts_match(expected: str, actual: str) -> bool:
        """Compare deux extraits en ignorant casse, ponctuation et diacritiques."""

        def normalize(s: str) -> str:
            if not s:
                return ''
            normalized = unicodedata.normalize('NFKD', s)
            normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
            normalized = re.sub(r'\s+', ' ', normalized).strip().casefold()
            return normalized

        def slim(s: str) -> str:
            return re.sub(r'[^0-9a-z]+', '', s)

        expected_norm = normalize(expected)
        actual_norm = normalize(actual)

        if expected_norm == actual_norm:
            return True

        return slim(expected_norm) == slim(actual_norm)

    @staticmethod
    def _find_best_span(text: str, entity_text: str, hint_start: Optional[int] = None) -> Optional[Tuple[int, int]]:
        """Trouve l'occurrence de entity_text la plus pertinente dans text."""

        if not entity_text:
            return None

        pattern = re.escape(entity_text)

        matches = list(re.finditer(pattern, text))
        if not matches:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))

        if not matches:
            return None

        if hint_start is None:
            target = matches[0]
        else:
            target = min(matches, key=lambda m: abs(m.start() - hint_start))

        return target.start(), target.end()

    def generate_brat_config(self, output_dir: str) -> None:
        """
        Génère les fichiers de configuration BRAT (annotation.conf et visual.conf)

        Args:
            output_dir: Répertoire de sortie
        """
        annotation_conf_path = os.path.join(output_dir, 'annotation.conf')
        visual_conf_path = os.path.join(output_dir, 'visual.conf')

        # Génération d'annotation.conf
        with open(annotation_conf_path, 'w', encoding='utf-8') as f:
            f.write('[entities]\n')
            for entity_type in sorted(self.entity_types):
                f.write(f'{entity_type}\n')

            f.write('\n[relations]\n')
            f.write('<OVERLAP>\tArg1:<ENTITY>, Arg2:<ENTITY>, <OVL-TYPE>:<ANY>\n')

            f.write('\n[events]\n')

            f.write('\n')

        # Génération d'visual.conf
        colors = [
            '#ffcccc', '#ccffcc', '#ccccff', '#ffffcc', '#ffccff', '#ccffff',
            '#ff9999', '#99ff99', '#9999ff', '#ffff99', '#ff99ff', '#99ffff',
            '#ff6666', '#66ff66', '#6666ff', '#ffff66', '#ff66ff', '#66ffff'
        ]

        with open(visual_conf_path, 'w', encoding='utf-8') as f:
            f.write('[labels]\n')
            for entity_type in sorted(self.entity_types):
                # Nom affiché plus lisible
                display_name = entity_type.replace('_', ' ')
                f.write(f'{entity_type} | {display_name}\n')

            f.write('\n[drawing]\n')
            for i, entity_type in enumerate(sorted(self.entity_types)):
                color = colors[i % len(colors)]
                f.write(f'{entity_type}\tbgColor:{color}\n')

        logger.info("Configuration BRAT générée :")
        logger.info(f"   • {annotation_conf_path}")
        logger.info(f"   • {visual_conf_path}")

    def convert_jsonl_to_brat(self, jsonl_file: str, output_dir: str,
                             prefix: str = "doc") -> None:
        """
        Convertit un fichier JSONL complet vers le format BRAT

        Args:
            jsonl_file: Fichier JSONL d'entrée
            output_dir: Répertoire de sortie BRAT
            prefix: Préfixe pour les noms de fichiers
        """
        # Création du répertoire de sortie
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Chargement des données
        documents = self.load_langextract_data(jsonl_file)

        if not documents:
            logger.warning("Aucun document à convertir")
            return

        # Conversion de chaque document
        converted_count = 0
        for i, document in enumerate(documents):
            doc_id = f"{prefix}_{i+1:03d}"

            try:
                txt_content, ann_content = self.convert_document(document, doc_id)

                # Sauvegarde des fichiers
                txt_path = os.path.join(output_dir, f"{doc_id}.txt")
                ann_path = os.path.join(output_dir, f"{doc_id}.ann")

                with open(txt_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(txt_content)

                with open(ann_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(ann_content)

                converted_count += 1
                logger.success(f"Converti : {doc_id} ({len(document.get('extractions', []))} entités)")

            except Exception as e:
                logger.error(f"Erreur pour document {i+1}: {e}")
                continue

        # Génération de la configuration BRAT
        if converted_count > 0:
            self.generate_brat_config(output_dir)

        logger.success("Conversion terminée !")
        logger.info(f"{converted_count}/{len(documents)} documents convertis")
        logger.info(f"Fichiers BRAT générés dans : {output_dir}")
        logger.info(f"{len(self.entity_types)} types d'entités")


    def print_statistics(self) -> None:
        """Affiche les statistiques de conversion"""
        logger.info("STATISTIQUES DE CONVERSION")
        logger.info("=" * 50)

        logger.info(f"Types d'entités ({len(self.entity_types)}) :")
        for entity_type in sorted(self.entity_types):
            logger.info(f"   • {entity_type}")




def main():
    """Fonction principale"""
    logger.info("CONVERSION LANGEXTRACT → BRAT")
    logger.info("=" * 50)

    # Utilisation des variables globales
    logger.info(f"Fichier d'entrée : {INPUT_JSONL_FILE}")
    logger.info(f"Répertoire de sortie : {OUTPUT_BRAT_DIR}")
    logger.info(f"Préfixe des fichiers : {FILE_PREFIX}")

    # Vérification du fichier d'entrée
    if not os.path.exists(INPUT_JSONL_FILE):
        logger.error(f"Fichier d'entrée non trouvé : {INPUT_JSONL_FILE}")
        return 1

    try:
        # Conversion
        converter = LangExtractToBratConverter()
        converter.convert_jsonl_to_brat(
            INPUT_JSONL_FILE,
            OUTPUT_BRAT_DIR,
            FILE_PREFIX
        )

        # Statistiques si demandées
        if SHOW_STATS:
            converter.print_statistics()

        logger.info("Pour utiliser avec BRAT :")
        logger.info(f"   1. Copiez {OUTPUT_BRAT_DIR}/ vers votre serveur BRAT")
        logger.info("   2. Configurez BRAT pour pointer vers ce répertoire")
        logger.info("   3. Les fichiers .txt et .ann sont prêts pour annotation")

        return 0

    except Exception as e:
        logger.error(f"Erreur lors de la conversion : {e}")
        return 1


if __name__ == "__main__":
    exit(main())
