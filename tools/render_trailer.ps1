# Renders the 60 s trailer: score (tools/gen_trailer_audio.py) -> frames (Godot Movie Maker,
# trailer/trailer.tscn) -> dist/GasingPangkah_Trailer.mp4 (H.264 + AAC, 1920x1080 @ 60).
#   tools/render_trailer.ps1                     final: 2x supersampled PNG frames, ~20 GB of temp space, ~30 min
#   tools/render_trailer.ps1 -Draft              quick review: 1x render to MJPEG -> *_draft.mp4
#   tools/render_trailer.ps1 -Draft -From 30 -Seconds 8
# Needs python with numpy, scipy, soundfile and imageio-ffmpeg (its bundled ffmpeg does the encode).
param(
	[string]$Godot = "E:\GodotProject\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe",
	[switch]$Draft,
	[double]$From = 0,
	[double]$Seconds = 60,
	[string]$Work = (Join-Path $env:TEMP "gasing_trailer")
)
$ErrorActionPreference = "Stop"
$inv = [Globalization.CultureInfo]::InvariantCulture
$root = Split-Path $PSScriptRoot -Parent
$score = Join-Path $root "trailer\trailer_score.wav"
python (Join-Path $root "tools\gen_trailer_audio.py")
if ($LASTEXITCODE -ne 0) { throw "score generation failed" }

$fromFrame = [int][math]::Round($From * 60)
$frames = [int][math]::Round($Seconds * 60)
$framesDir = Join-Path $Work "frames"
$repairDir = Join-Path $Work "repair"
$log = Join-Path $Work "godot.log"
New-Item -ItemType Directory -Force $framesDir, $repairDir | Out-Null
Get-ChildItem $framesDir, $repairDir -Filter "*.png" | Remove-Item -Force
$movie = if ($Draft) { Join-Path $Work "draft.avi" } else { Join-Path $framesDir "f.png" }

function Invoke-Movie([string]$out, [int]$startFrame, [int]$count) {
	# Movie Maker records at the window size, which project.godot pins to 1600x900: a temporary override.cfg
	# sizes the window to 1920x1080 and parks it off-screen, so nothing covers or minimizes it mid-render
	# (a minimized window is not drawn, and Movie Maker then repeats the last image)
	$override = Join-Path $root "override.cfg"
	if (Test-Path $override) { throw "$override already exists; refusing to overwrite it" }
	Set-Content -Path $override -Encoding ascii -Value ("[display]`n`nwindow/size/window_width_override=1920`n" +
		"window/size/window_height_override=1080`nwindow/size/initial_position_type=0`nwindow/size/initial_position=Vector2i(-4000, 0)`n")
	$env:GODOT_MCP_HEADLESS_CHILD = "1" # the MCP autoloads stay idle in this child process
	$extra = @("--from-frame=$startFrame")
	if ($Draft) { $extra += "--draft" }
	try {
		& $Godot --path $root --fixed-fps 60 --write-movie $out --quit-after $count res://trailer/trailer.tscn -- @extra 2>&1 |
			ForEach-Object { "$_" } | Tee-Object -FilePath $log -Append
	} finally {
		Remove-Item $override -Force
	}
}

function Find-Undrawn {
	# film grain is reseeded every frame, so a frame byte-identical to the one before it was never drawn
	$bad = [Collections.Generic.List[int]]::new()
	$prev = $null
	for ($k = 0; $k -lt $frames; $k++) {
		$f = Get-Item (Join-Path $framesDir ("f{0:D8}.png" -f $k))
		if ($null -ne $prev -and $f.Length -eq $prev.Length -and
				(Get-FileHash $f.FullName -Algorithm MD5).Hash -eq (Get-FileHash $prev.FullName -Algorithm MD5).Hash) {
			$bad.Add($fromFrame + $k)
		}
		$prev = $f
	}
	return ,$bad
}

Remove-Item $log -ErrorAction SilentlyContinue
Invoke-Movie $movie $fromFrame $frames
if (-not $Draft) {
	$shots = ((Select-String -Path $log -Pattern "^TRAILER_SHOTS (.+)$").Matches[0].Groups[1].Value -split ",") | ForEach-Object { [int]$_ }
	for ($try = 1; ; $try++) {
		$bad = Find-Undrawn
		if ($bad.Count -eq 0) { break }
		if ($try -gt 3) { throw "frames still undrawn after 3 repair passes: $($bad -join ',')" }
		Write-Host "repair pass ${try}: $($bad.Count) undrawn frames"
		# re-render each affected shot from its first frame, so every event in it replays exactly
		foreach ($g in ($bad | Group-Object { $k = $_; ($shots | Where-Object { $_ -le $k } | Measure-Object -Maximum).Maximum })) {
			$s = [math]::Max([int]$g.Name, $fromFrame)
			$last = ($g.Group | Measure-Object -Maximum).Maximum
			Get-ChildItem $repairDir -Filter "*.png" | Remove-Item -Force
			Invoke-Movie (Join-Path $repairDir "r.png") $s ($last - $s + 1)
			foreach ($k in $g.Group) {
				Copy-Item (Join-Path $repairDir ("r{0:D8}.png" -f ($k - $s))) (Join-Path $framesDir ("f{0:D8}.png" -f ($k - $fromFrame))) -Force
			}
		}
	}
}

$ffmpeg = python -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())"
$distDir = Join-Path $root "dist"
New-Item -ItemType Directory -Force $distDir | Out-Null
$out = Join-Path $distDir ($(if ($Draft) { "GasingPangkah_Trailer_draft.mp4" } else { "GasingPangkah_Trailer.mp4" }))
$video = if ($Draft) { @("-i", $movie) } else { @("-framerate", "60", "-i", (Join-Path $framesDir "f%08d.png")) }
# tag BT.709 explicitly, or players shift the ambers
& $ffmpeg -y -hide_banner -loglevel warning @video -ss $From.ToString($inv) -t $Seconds.ToString($inv) -i $score -map 0:v -map 1:a -frames:v $frames `
	-vf "scale=out_color_matrix=bt709:out_range=tv" -c:v libx264 -preset $(if ($Draft) { "veryfast" } else { "slow" }) `
	-crf $(if ($Draft) { 22 } else { 16 }) -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 `
	-c:a aac -b:a 256k -movflags +faststart $out
if ($LASTEXITCODE -ne 0) { throw "ffmpeg failed" }
if (-not $Draft) { Get-ChildItem $framesDir, $repairDir -Filter "*.png" | Remove-Item -Force }
Write-Host "wrote $out"
