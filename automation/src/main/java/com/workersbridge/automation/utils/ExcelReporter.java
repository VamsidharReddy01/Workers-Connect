package com.workersbridge.automation.utils;

import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.FileOutputStream;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class ExcelReporter {

    public static void generateReport(List<Map<String, String>> testResults, String outputPath) {
        try (Workbook workbook = new XSSFWorkbook()) {
            Sheet sheet = workbook.createSheet("Executed Test Cases");
            
            // Create Header Row
            Row headerRow = sheet.createRow(0);
            String[] headers = {"Test ID", "Module", "Test Name", "Priority", "Status", "Execution Time"};
            for (int i = 0; i < headers.length; i++) {
                Cell cell = headerRow.createCell(i);
                cell.setCellValue(headers[i]);
                CellStyle style = workbook.createCellStyle();
                Font font = workbook.createFont();
                font.setBold(true);
                style.setFont(font);
                cell.setCellStyle(style);
            }

            // Populate Data
            int rowNum = 1;
            for (Map<String, String> result : testResults) {
                Row row = sheet.createRow(rowNum++);
                row.createCell(0).setCellValue(result.getOrDefault("Test ID", ""));
                row.createCell(1).setCellValue(result.getOrDefault("Module", ""));
                row.createCell(2).setCellValue(result.getOrDefault("Test Name", ""));
                row.createCell(3).setCellValue(result.getOrDefault("Priority", ""));
                row.createCell(4).setCellValue(result.getOrDefault("Status", ""));
                row.createCell(5).setCellValue(result.getOrDefault("Execution Time", ""));
            }

            for (int i = 0; i < headers.length; i++) {
                sheet.autoSizeColumn(i);
            }

            try (FileOutputStream fileOut = new FileOutputStream(outputPath)) {
                workbook.write(fileOut);
            }
            System.out.println("Excel Report generated at: " + outputPath);

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
