import * as XLSX from 'xlsx'

export function exportToExcel(data, headers, filename = 'export.xlsx') {
  const wsData = [headers, ...data]
  const ws = XLSX.utils.aoa_to_sheet(wsData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
  XLSX.writeFile(wb, filename)
}

export function exportCsvToExcel(csvContent, filename = 'export.xlsx') {
  const wb = XLSX.read(csvContent, { type: 'string' })
  XLSX.writeFile(wb, filename)
}

export function exportStatsToExcel(exportData, filename) {
  if (exportData.csv_content) {
    exportCsvToExcel(exportData.csv_content, exportData.filename || filename)
  }
}
