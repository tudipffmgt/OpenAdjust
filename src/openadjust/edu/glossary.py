"""
Glossary of geodetic adjustment terms with explanations.

Each entry contains:
- term: The technical term
- short: Brief tooltip description
- long: Detailed explanation with formulas
- related: Related terms
"""

GLOSSARY = {
    "sigma_0": {
        "term": "σ₀ (Sigma Null)",
        "short": "A-posteriori Standardabweichung der Gewichtseinheit",
        "long": """
<h2>σ₀ - Standardabweichung der Gewichtseinheit</h2>

<p>Die <b>a-posteriori Standardabweichung der Gewichtseinheit</b> ist ein Maß für die 
Qualität der Ausgleichung und des stochastischen Modells.</p>

<h3>Berechnung</h3>
<p>
σ₀ = √(v'Pv / r)
</p>
<p>wobei:</p>
<ul>
    <li><b>v</b> = Verbesserungsvektor (Residuen)</li>
    <li><b>P</b> = Gewichtsmatrix</li>
    <li><b>r</b> = Redundanz (Anzahl Beobachtungen - Anzahl Unbekannte)</li>
</ul>

<h3>Interpretation</h3>
<ul>
    <li><b>σ₀ ≈ 1</b>: Das stochastische Modell passt gut zu den Beobachtungen</li>
    <li><b>σ₀ > 1</b>: Die a-priori Genauigkeiten waren zu optimistisch oder es gibt grobe Fehler</li>
    <li><b>σ₀ < 1</b>: Die a-priori Genauigkeiten waren zu pessimistisch</li>
</ul>

<h3>Literatur</h3>
<p>Niemeier (2008): Ausgleichungsrechnung, Kapitel 3.5</p>
""",
        "related": ["globaltest", "redundanz", "gewichtsmatrix"]
    },

    "globaltest": {
        "term": "Globaler Modelltest",
        "short": "Chi-Quadrat-Test zur Prüfung des gesamten stochastischen Modells",
        "long": """
<h2>Globaler Modelltest (Chi-Quadrat-Test)</h2>

<p>Der <b>globale Modelltest</b> prüft, ob das stochastische Modell 
(die a-priori Genauigkeitsannahmen) mit den tatsächlichen Beobachtungen verträglich ist.</p>

<h3>Hypothesen</h3>
<ul>
    <li><b>H₀</b>: σ₀ = σ₀,a-priori (Modell ist korrekt)</li>
    <li><b>H₁</b>: σ₀ ≠ σ₀,a-priori (Modell ist nicht korrekt)</li>
</ul>

<h3>Testgröße</h3>
<p>
T = v'Pv / σ₀,a-priori²
</p>
<p>folgt einer χ²-Verteilung mit r Freiheitsgraden.</p>

<h3>Testentscheidung</h3>
<p>Der Test wird <b>bestanden</b>, wenn:</p>
<p>χ²(α/2, r) ≤ T ≤ χ²(1-α/2, r)</p>
<p>mit Signifikanzniveau α (typisch 0.05).</p>

<h3>Interpretation</h3>
<ul>
    <li><b>Test bestanden</b>: Keine signifikanten Abweichungen vom Modell</li>
    <li><b>Test nicht bestanden</b>: Mögliche Ursachen:
        <ul>
            <li>Falsche a-priori Genauigkeiten</li>
            <li>Grobe Fehler in den Beobachtungen</li>
            <li>Falsches funktionales Modell</li>
        </ul>
    </li>
</ul>
""",
        "related": ["sigma_0", "redundanz", "ausreissertest"]
    },

    "redundanz": {
        "term": "Redundanz",
        "short": "Anzahl überschüssiger Beobachtungen (n - u)",
        "long": """
<h2>Redundanz (Freiheitsgrade)</h2>

<p>Die <b>Redundanz</b> r ist die Differenz zwischen der Anzahl der Beobachtungen 
und der Anzahl der Unbekannten:</p>

<h3>Formel</h3>
<p>
r = n - u
</p>
<p>wobei:</p>
<ul>
    <li><b>n</b> = Anzahl der Beobachtungen</li>
    <li><b>u</b> = Anzahl der Unbekannten (Parameter)</li>
</ul>

<h3>Bedeutung</h3>
<ul>
    <li><b>r = 0</b>: Keine Redundanz, keine Kontrolle möglich</li>
    <li><b>r > 0</b>: Überbestimmtes System, Ausgleichung möglich</li>
    <li><b>r < 0</b>: Unterbestimmtes System, keine eindeutige Lösung</li>
</ul>

<h3>Partielle Redundanz</h3>
<p>Jede Beobachtung hat eine <b>partielle Redundanz</b> rᵢ (0 ≤ rᵢ ≤ 1), 
die angibt, wie gut die Beobachtung kontrolliert ist.</p>
""",
        "related": ["sigma_0", "globaltest"]
    },

    "fehlerellipse": {
        "term": "Fehlerellipse",
        "short": "Grafische Darstellung der 2D-Positionsgenauigkeit eines Punktes",
        "long": """
<h2>Fehlerellipse</h2>

<p>Die <b>Fehlerellipse</b> ist eine grafische Darstellung der Unsicherheit 
einer 2D-Position. Sie wird aus der Kofaktormatrix Qxx berechnet.</p>

<h3>Berechnung</h3>
<p>Für einen Punkt mit Kofaktormatrix:</p>
<p>
Q = [[qxx, qxy], [qxy, qyy]]
</p>
<p>werden die Halbachsen aus den Eigenwerten λ₁, λ₂ berechnet:</p>
<ul>
    <li><b>A</b> = σ₀ · √λ₁ (große Halbachse)</li>
    <li><b>B</b> = σ₀ · √λ₂ (kleine Halbachse)</li>
</ul>

<h3>Orientierung</h3>
<p>Die Richtung der großen Halbachse ergibt sich aus dem Eigenvektor 
zum größten Eigenwert.</p>

<h3>Helmert-Punktlagefehler</h3>
<p>
sH = √(σx² + σy²)
</p>
<p>ist ein skalares Maß für die Positionsgenauigkeit.</p>
""",
        "related": ["qxx_matrix", "sigma_0", "helmert_fehler"]
    },

    "qxx_matrix": {
        "term": "Kofaktormatrix Qxx",
        "short": "Matrix der Kofaktoren der ausgeglichenen Parameter",
        "long": """
<h2>Kofaktormatrix Qxx</h2>

<p>Die <b>Kofaktormatrix Qxx</b> enthält die Varianzen und Kovarianzen 
der ausgeglichenen Parameter, skaliert mit 1/σ₀².</p>

<h3>Berechnung</h3>
<p>
Qxx = (A'PA)⁻¹ = N⁻¹
</p>
<p>wobei:</p>
<ul>
    <li><b>A</b> = Designmatrix (Jacobi-Matrix)</li>
    <li><b>P</b> = Gewichtsmatrix</li>
    <li><b>N</b> = Normalgleichungsmatrix</li>
</ul>

<h3>Kovarianzmatrix</h3>
<p>Die vollständige Kovarianzmatrix ist:</p>
<p>
Σxx = σ₀² · Qxx
</p>

<h3>Diagonalelemente</h3>
<p>Die Diagonalelemente qᵢᵢ liefern die Standardabweichungen:</p>
<p>
σᵢ = σ₀ · √qᵢᵢ
</p>
""",
        "related": ["designmatrix", "normalgleichung", "fehlerellipse"]
    },

    "designmatrix": {
        "term": "Designmatrix A",
        "short": "Matrix der partiellen Ableitungen (Jacobi-Matrix)",
        "long": """
<h2>Designmatrix (Jacobi-Matrix)</h2>

<p>Die <b>Designmatrix A</b> enthält die partiellen Ableitungen 
der Beobachtungsgleichungen nach den unbekannten Parametern.</p>

<h3>Aufbau</h3>
<p>
A = [∂f/∂x₁, ∂f/∂x₂, ..., ∂f/∂xᵤ]
</p>
<ul>
    <li>Zeilen: Beobachtungen (n)</li>
    <li>Spalten: Unbekannte Parameter (u)</li>
</ul>

<h3>Beispiel: Streckenbeobachtung</h3>
<p>Für eine Strecke s zwischen Punkten i und j:</p>
<p>
∂s/∂xᵢ = -(xⱼ-xᵢ)/s<br>
∂s/∂yᵢ = -(yⱼ-yᵢ)/s<br>
∂s/∂xⱼ = (xⱼ-xᵢ)/s<br>
∂s/∂yⱼ = (yⱼ-yᵢ)/s
</p>
""",
        "related": ["qxx_matrix", "normalgleichung"]
    },

    "normalgleichung": {
        "term": "Normalgleichung",
        "short": "Lineares Gleichungssystem N·x = n zur Parameterbestimmung",
        "long": """
<h2>Normalgleichungssystem</h2>

<p>Das <b>Normalgleichungssystem</b> entsteht durch Anwendung der Methode 
der kleinsten Quadrate auf das Gauß-Markov-Modell.</p>

<h3>Herleitung</h3>
<p>Aus dem Beobachtungsmodell l + v = Ax wird durch Minimierung von v'Pv:</p>
<p>
N · x = n
</p>
<p>mit:</p>
<ul>
    <li><b>N</b> = A'PA (Normalgleichungsmatrix)</li>
    <li><b>n</b> = A'Pl (rechte Seite)</li>
    <li><b>l</b> = Beobachtungsvektor (reduziert: l - l₀)</li>
</ul>

<h3>Lösung</h3>
<p>
x = N⁻¹ · n = (A'PA)⁻¹ · A'Pl
</p>
""",
        "related": ["designmatrix", "qxx_matrix", "gauss_markov"]
    },

    "gauss_markov": {
        "term": "Gauß-Markov-Modell",
        "short": "Mathematisches Modell der vermittelnden Ausgleichung",
        "long": """
<h2>Gauß-Markov-Modell</h2>

<p>Das <b>Gauß-Markov-Modell</b> ist das mathematische Fundament 
der vermittelnden Ausgleichung (parametric adjustment).</p>

<h3>Funktionales Modell</h3>
<p>
l + v = A · x
</p>
<p>wobei:</p>
<ul>
    <li><b>l</b> = Beobachtungsvektor (gemessen - genähert)</li>
    <li><b>v</b> = Verbesserungsvektor (Residuen)</li>
    <li><b>A</b> = Designmatrix</li>
    <li><b>x</b> = Parameterkorrekturvektor</li>
</ul>

<h3>Stochastisches Modell</h3>
<p>
E{l} = Ax (Erwartungswert)<br>
Σll = σ₀² · Qll = σ₀² · P⁻¹ (Kovarianzmatrix)
</p>

<h3>Zielfunktion</h3>
<p>Minimiere: v'Pv → min</p>
<p>(gewichtete Quadratsumme der Verbesserungen)</p>
""",
        "related": ["normalgleichung", "sigma_0"]
    },

    "gewichtsmatrix": {
        "term": "Gewichtsmatrix P",
        "short": "Diagonalmatrix mit Gewichten p = 1/σ² der Beobachtungen",
        "long": """
<h2>Gewichtsmatrix P</h2>

<p>Die <b>Gewichtsmatrix P</b> beschreibt die stochastischen Eigenschaften 
der Beobachtungen.</p>

<h3>Definition</h3>
<p>Für unkorrelierte Beobachtungen:</p>
<p>
P = diag(p₁, p₂, ..., pₙ)
</p>
<p>mit Gewichten:</p>
<p>
pᵢ = σ₀² / σᵢ² = 1 / σᵢ² (bei σ₀ = 1)
</p>

<h3>Bedeutung</h3>
<ul>
    <li>Höheres Gewicht = präzisere Beobachtung = mehr Einfluss</li>
    <li>Gewicht = 0: Beobachtung wird nicht verwendet</li>
</ul>

<h3>Beispiel: Streckenmessung</h3>
<p>σ = 2mm + 1ppm → p = 1/(0.002 + 1e-6·s)²</p>
""",
        "related": ["sigma_0", "gauss_markov"]
    },

    "helmert_fehler": {
        "term": "Helmert-Punktlagefehler",
        "short": "Skalares Maß für die 2D-Positionsgenauigkeit: sH = √(σx² + σy²)",
        "long": """
<h2>Helmert-Punktlagefehler sH</h2>

<p>Der <b>Helmert-Punktlagefehler</b> ist ein eindimensionales Maß 
für die Lagegenauigkeit eines Punktes.</p>

<h3>Formel (2D)</h3>
<p>
sH = √(σx² + σy²)
</p>

<h3>Formel (3D)</h3>
<p>
sH = √(σx² + σy² + σz²)
</p>

<h3>Bedeutung</h3>
<p>Der Helmert-Fehler entspricht dem Radius eines Kreises (2D) oder 
einer Kugel (3D), der/die etwa 39% Wahrscheinlichkeit enthält.</p>

<h3>Konfidenzbereich</h3>
<ul>
    <li>1·sH: ~39% Wahrscheinlichkeit (2D)</li>
    <li>2·sH: ~86% Wahrscheinlichkeit (2D)</li>
    <li>2.45·sH: ~95% Wahrscheinlichkeit (2D)</li>
</ul>
""",
        "related": ["fehlerellipse", "sigma_0"]
    },

    "verbesserung": {
        "term": "Verbesserung (Residuum)",
        "short": "Differenz zwischen ausgeglichener und gemessener Beobachtung",
        "long": """
<h2>Verbesserungen (Residuen)</h2>

<p>Die <b>Verbesserungen v</b> sind die Differenzen zwischen den 
aus den ausgeglichenen Koordinaten berechneten und den gemessenen Beobachtungen.</p>

<h3>Definition</h3>
<p>
v = l_ausgeglichen - l_gemessen = A·x - l
</p>

<h3>Eigenschaften</h3>
<ul>
    <li>A'Pv = 0 (Normalgleichungs-Bedingung)</li>
    <li>E{v} = 0 (Erwartungswert = 0)</li>
    <li>Σvv = σ₀² · Qvv (Kovarianzmatrix der Verbesserungen)</li>
</ul>

<h3>Normierte Verbesserung</h3>
<p>
w = v / (σ₀ · √qvv)
</p>
<p>Werte |w| > 3 deuten auf Ausreißer hin.</p>
""",
        "related": ["sigma_0", "ausreissertest"]
    },

    "ausreissertest": {
        "term": "Ausreißertest",
        "short": "Statistischer Test zur Identifikation grober Fehler",
        "long": """
<h2>Ausreißertest (Data Snooping)</h2>

<p>Der <b>Ausreißertest</b> identifiziert Beobachtungen mit möglicherweise 
groben Fehlern anhand der normierten Verbesserungen.</p>

<h3>Normierte Verbesserung</h3>
<p>
wᵢ = vᵢ / (σ₀ · √qvvᵢ)
</p>

<h3>Testentscheidung</h3>
<ul>
    <li>|wᵢ| ≤ 3: Beobachtung unauffällig</li>
    <li>|wᵢ| > 3: Verdacht auf Ausreißer (~0.3% bei Normalverteilung)</li>
    <li>|wᵢ| > 4: Starker Verdacht auf groben Fehler</li>
</ul>

<h3>Vorgehen bei Ausreißern</h3>
<ol>
    <li>Beobachtung prüfen (Messfehler? Eingabefehler?)</li>
    <li>Falls keine Erklärung: Gewicht reduzieren oder deaktivieren</li>
    <li>Ausgleichung wiederholen</li>
</ol>
""",
        "related": ["verbesserung", "globaltest"]
    },
}


def get_tooltip(term_id: str) -> str:
    """Returns the short tooltip text for a term."""
    if term_id in GLOSSARY:
        return GLOSSARY[term_id]["short"]
    return ""


def get_full_explanation(term_id: str) -> str:
    """Returns the full HTML explanation for a term."""
    if term_id in GLOSSARY:
        return GLOSSARY[term_id]["long"]
    return f"<p>Keine Erklärung für '{term_id}' verfügbar.</p>"


def get_related_terms(term_id: str) -> list[str]:
    """Returns list of related term IDs."""
    if term_id in GLOSSARY:
        return GLOSSARY[term_id].get("related", [])
    return []
