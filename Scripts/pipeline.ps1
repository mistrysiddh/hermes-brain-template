# pipeline.ps1 – daily trend digest via Ollama embeddings (no sentence-transformers needed)
param(
    [string]$Vault   = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Query   = "local LLM agents offline",
    [int]$TopN       = 5,
    [string]$OutDir  = "$Vault\Research\Trend-Digest",
    [string]$OllamaHost = "http://127.0.0.1:11434",
    [string]$EmbedModel = "nomic-embed-text"
)

# Ensure output folder
if (!(Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

# Function to get embedding from Ollama
function Get-OllamaEmbedding {
    param([string]$Text)
    $payload = @{
        model = $EmbedModel
        prompt = $Text
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Method Post -Uri "$OllamaHost/api/embeddings" -Body $payload -ContentType "application/json"
    return $response.embedding
}

# Read all .md files in vault
$notes = Get-ChildItem -Path $Vault -Filter *.md -Recurse | Select-Object -ExpandProperty FullName
if ($notes.Count -eq 0) {
    Write-Error "No markdown notes found in $Vault"
    exit 1
}

Write-Host "Found $($notes.Count) notes. Computing embeddings (this may take a while)..."

# Compute query embedding
$queryEmbedding = Get-OllamaEmbedding -Text $Query

# Function cosine similarity
function CosineSimilarity {
    param([double[]]$a, [double[]]$b)
    $dot = 0
    $normA = 0
    $normB = 0
    for ($i = 0; $i -lt $a.Count; $i++) {
        $dot += $a[$i] * $b[$i]
        $normA += $a[$i] * $a[$i]
        $normB += $b[$i] * $b[$i]
    }
    return $dot / ([math]::Sqrt($normA) * [math]::Sqrt($normB))
}

$results = @()
foreach ($notePath in $notes) {
    try {
        $content = Get-Content -Path $notePath -Raw
        if ([string]::IsNullOrWhiteSpace($content)) { continue }
        $emb = Get-OllamaEmbedding -Text $content
        $score = CosineSimilarity -a $queryEmbedding -b $emb
        $relPath = (Resolve-Path -Relative -Path $notePath).Path
        $snippet = $content.Substring(0, [math]::Min(200, $content.Length)).Replace("`r`n", " ").Replace("`n", " ")
        $results += [pscustomobject]@{
            Path = $relPath
            Score = $score
            Snippet = $snippet
        }
    } catch {
        Write-Warning "Failed to process $notePath"
    }
}

# Sort and take top N
$top = $results | Sort-Object Score -Descending | Select-Object -First $TopN

# Build markdown
$today = Get-Date -Format "yyyy-MM-dd"
$outFile = Join-Path $OutDir "$today.md"

$header = "# Trend Digest - $today`n## Query: $Query`n| Score | Note | Snippet |`n|-------|------|---------|"
$header | Out-File -FilePath $outFile -Encoding UTF8

foreach ($r in $top) {
    $line = "| {0:F3} | [[{1}]] | {2} |" -f $r.Score, ($r.Path -replace '\\','/'), $r.Snippet
    $line | Out-File -FilePath $outFile -Append -Encoding UTF8
}

Write-Host "Digest written to $outFile"