# Render editable slides using the existing PowerPoint installation. Author: eula.
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskSpec = Get-Content -LiteralPath (Join-Path $taskRoot 'assignment\.cache\presentation-redesign\presentation_spec.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskOut = Join-Path $taskRoot 'assignment\deliverables'
$taskScale = 2.0 / 3.0
function Get-TaskColor([string]$hex) {
    return [Convert]::ToInt32($hex.Substring(0,2),16) + 256 * [Convert]::ToInt32($hex.Substring(2,2),16) + 65536 * [Convert]::ToInt32($hex.Substring(4,2),16)
}
$taskApp = New-Object -ComObject PowerPoint.Application
$taskApp.Visible = -1
$taskApp.WindowState = 2
$taskDeck = $null
$taskOverflow = @()
try {
    $taskDeck = $taskApp.Presentations.Add(0)
    $taskDeck.PageSetup.SlideWidth = [single]($taskSpec.width * $taskScale)
    $taskDeck.PageSetup.SlideHeight = [single]($taskSpec.height * $taskScale)
    foreach ($taskPage in $taskSpec.slides) {
        $taskSlide = $taskDeck.Slides.Add($taskDeck.Slides.Count + 1,12)
        $taskIndex = 0
        foreach ($taskShape in $taskPage.shapes) {
            $taskIndex++
            $taskX=[single]($taskShape.x*$taskScale); $taskY=[single]($taskShape.y*$taskScale)
            $taskW=[single]($taskShape.w*$taskScale); $taskH=[single]($taskShape.h*$taskScale)
            if ($taskShape.kind -eq 'line') {
                $taskItem=$taskSlide.Shapes.AddLine($taskX,$taskY,($taskX+$taskW),($taskY+$taskH))
                $taskItem.Line.ForeColor.RGB=Get-TaskColor $taskShape.color
                $taskItem.Line.Weight=[single]($taskShape.width*$taskScale)
            } elseif ($taskShape.kind -eq 'rect') {
                $taskType=1; if ($taskShape.rounded) { $taskType=5 }
                $taskItem=$taskSlide.Shapes.AddShape($taskType,$taskX,$taskY,$taskW,$taskH)
                $taskItem.Fill.ForeColor.RGB=Get-TaskColor $taskShape.fill
                if ($taskShape.border) { $taskItem.Line.ForeColor.RGB=Get-TaskColor $taskShape.border } else { $taskItem.Line.Visible=0 }
                if ($taskShape.rounded) { $taskItem.Adjustments.Item(1)=0.09 }
            } elseif ($taskShape.kind -eq 'text') {
                $taskItem=$taskSlide.Shapes.AddTextbox(1,$taskX,$taskY,$taskW,$taskH)
                $taskItem.Line.Visible=0; $taskItem.Fill.Visible=0
                $taskFrame=$taskItem.TextFrame
                $taskFrame.MarginLeft=0; $taskFrame.MarginRight=0; $taskFrame.MarginTop=0; $taskFrame.MarginBottom=0
                $taskFrame.WordWrap=-1; $taskFrame.AutoSize=0
                $taskRange=$taskFrame.TextRange
                $taskRange.Text=$taskShape.text
                $taskRange.Font.Name=$taskShape.font
                $taskRange.Font.Size=[single]($taskShape.size*$taskScale)
                $taskRange.Font.Bold=0; if ($taskShape.bold) { $taskRange.Font.Bold=-1 }
                $taskRange.Font.Color.RGB=Get-TaskColor $taskShape.color
                $taskRange.ParagraphFormat.SpaceBefore=0; $taskRange.ParagraphFormat.SpaceAfter=0
                $taskRange.ParagraphFormat.SpaceWithin=1.05
                $taskRange.ParagraphFormat.Alignment=1
                if ($taskShape.align -eq 'right') { $taskRange.ParagraphFormat.Alignment=3 }
                if ($taskShape.align -eq 'center') { $taskRange.ParagraphFormat.Alignment=2 }
                if ($taskRange.BoundHeight -gt ($taskH+1)) {
                    $taskOverflow+=@{slide=$taskSlide.SlideIndex;shape=$taskIndex;text=$taskShape.text;height=$taskH;actual=$taskRange.BoundHeight}
                }
            }
        }
        $taskSlide.NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text = ('Author: eula' + "`r`n" + $taskPage.time + "`r`n" + $taskPage.direction + "`r`n`r`n" + $taskPage.notes)
        $taskSlide.SlideShowTransition.AdvanceOnClick=-1
        $taskSlide.SlideShowTransition.AdvanceOnTime=0
    }
    $taskDeck.SaveAs((Join-Path $taskOut 'FTEC5660_Presentation.pptx'),24)
    $taskDeck.SaveAs((Join-Path $taskOut 'FTEC5660_Presentation.pdf'),32)
    ConvertTo-Json -InputObject @($taskOverflow) -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot 'assignment\.cache\presentation-redesign\overflow.json') -Encoding UTF8
    Write-Output ('Slides rendered: ' + $taskDeck.Slides.Count)
    Write-Output ('Text boxes requiring review: ' + $taskOverflow.Count)
} finally {
    if ($null -ne $taskDeck) { $taskDeck.Close() }
    if ($taskApp.Presentations.Count -eq 0) { $taskApp.Quit() }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskApp)
}
