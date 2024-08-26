def highlight_differences(self, doc, words1, words2, page_num):
    differences = []
    current_diff = []

    if page_num < len(words1) and page_num < len(words2):
        words1_set = set((word[4] for word in words1[page_num] if isinstance(word[4], str)))
        words2_set = set((word[4] for word in words2[page_num] if isinstance(word[4], str)))

        for word1 in words1[page_num]:
            if isinstance(word1, list) and len(word1) >= 5:  # Asegúrate de que word1 es una lista con al menos 5 elementos
                if word1[4] not in words2_set:
                    if current_diff and (int(word1[0]) > int(current_diff[-1][2]) + 10):  # Verifica si las palabras no son consecutivas
                        differences.append(current_diff)
                        current_diff = []
                    current_diff.append(word1)
                    highlight = fitz.Rect(word1[:4])
                    doc[page_num].add_highlight_annot(highlight)
                else:
                    if current_diff:
                        differences.append(current_diff)
                        current_diff = []
        if current_diff:
            differences.append(current_diff)
    elif page_num < len(words1):  # Caso donde solo hay texto en el primer PDF
        for word1 in words1[page_num]:
            if isinstance(word1, list) and len(word1) >= 5:
                current_diff.append(word1)
                highlight = fitz.Rect(word1[:4])
                doc[page_num].add_highlight_annot(highlight)
        differences.append(current_diff)
        self.pdf1_diff_edit.setText(f"Texto encontrado en PDF1 pero no en PDF2:\n{' '.join([word[4] for word in current_diff if isinstance(word[4], str)])}")
    elif page_num < len(words2):  # Caso donde solo hay texto en el segundo PDF
        for word2 in words2[page_num]:
            if isinstance(word2, list) and len(word2) >= 5:
                current_diff.append(word2)
                highlight = fitz.Rect(word2[:4])
                doc[page_num].add_highlight_annot(highlight)
        differences.append(current_diff)
        self.pdf2_diff_edit.setText(f"Texto encontrado en PDF2 pero no en PDF1:\n{' '.join([word[4] for word in current_diff if isinstance(word[4], str)])}")

    self.total_diffs += len(differences)  # Acumular diferencias totales
    return doc, differences
