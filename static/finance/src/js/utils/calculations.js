/**
 * CALCULATIONS MANAGER v2.0
 * Berfungsi sebagai wrapper untuk FormulaEngine agar tetap kompatibel dengan kode lama.
 */
class CalculationsManager {
    constructor() {
        // formulaEngine didefinisikan di js/engine/formula.js
    }

    calculateRow(row) {
        if (!window.formulaEngine) return row;

        if (row && row.formulas && typeof row.formulas === 'string') {
            try { row.formulas = JSON.parse(row.formulas); } catch (e) { row.formulas = null; }
        }

        const newRow = { ...row };

        // Get active sheet configuration from tableManager if available
        const config = (window.tableManager && window.tableManager.sheetConfig) || {};

        const hasFormula = (field) => {
            if (window.formulaEngine && window.formulaEngine.isRowExcludedForField(newRow, field)) return true;
            return newRow.formulas && newRow.formulas[field] !== undefined;
        };

        // Kolom Penjualan
        const penjualanCfg = config.penjualan || { autoCalc: true, template: 'standard_cargo' };
        if (penjualanCfg.autoCalc && !hasFormula('penjualan')) {
            if (penjualanCfg.formula) {
                newRow.penjualan = window.formulaEngine.evaluateCustomFormula(penjualanCfg.formula, newRow);
            } else {
                newRow.penjualan = window.formulaEngine.compute('penjualan', newRow, { template: penjualanCfg.template });
            }
        }
        
        // Kolom Total Biaya
        const totalBiayaCfg = config.total_biaya || { autoCalc: true, template: 'vendor_ops' };
        if (totalBiayaCfg.autoCalc && !hasFormula('total_biaya')) {
            if (totalBiayaCfg.formula) {
                newRow.total_biaya = window.formulaEngine.evaluateCustomFormula(totalBiayaCfg.formula, newRow);
            } else {
                newRow.total_biaya = window.formulaEngine.compute('total_biaya', newRow, { template: totalBiayaCfg.template });
            }
        }
        
        // Kolom Asuransi
        const asuransiCfg = config.asuransi || { autoCalc: true, template: 'nilai_barang_02' };
        if (asuransiCfg.autoCalc && !hasFormula('asuransi')) {
            if (asuransiCfg.formula) {
                newRow.asuransi = window.formulaEngine.evaluateCustomFormula(asuransiCfg.formula, newRow);
            } else {
                newRow.asuransi = window.formulaEngine.compute('asuransi', newRow, { template: asuransiCfg.template });
            }
        }
        
        // Kolom Asuransi Jasindo
        const jasindoCfg = config.asuransi_jasindo || { autoCalc: true, template: 'nilai_barang_01' };
        if (jasindoCfg.autoCalc && !hasFormula('asuransi_jasindo')) {
            if (jasindoCfg.formula) {
                newRow.asuransi_jasindo = window.formulaEngine.evaluateCustomFormula(jasindoCfg.formula, newRow);
            } else {
                newRow.asuransi_jasindo = window.formulaEngine.compute('asuransi_jasindo', newRow, { template: jasindoCfg.template });
            }
        }
        
        // Kolom Profit
        const profitCfg = config.profit || { autoCalc: true, template: 'penjualan_minus_cost' };
        if (profitCfg.autoCalc && !hasFormula('profit')) {
            if (profitCfg.formula) {
                newRow.profit = window.formulaEngine.evaluateCustomFormula(profitCfg.formula, newRow);
            } else {
                newRow.profit = window.formulaEngine.compute('profit', newRow, { template: profitCfg.template });
            }
        }
        
        // Kolom Margin Percent (IDX Profit)
        const idxProfitCfg = config.idx_profit || { autoCalc: true };
        if (idxProfitCfg.autoCalc && !hasFormula('idx_profit')) {
            newRow.idx_profit = window.formulaEngine.compute('margin_percent', newRow);
        }

        return newRow;
    }

    calculateAllMetrics(data) {
        return data.map(row => this.calculateRow(row));
    }

    getSummaryStats(data) {
        if (!window.formulaEngine) return { totalRevenue: 0, totalCost: 0, totalProfit: 0, totalShipments: 0 };

        let totalRevenue = 0, totalCost = 0, totalProfit = 0, count = 0;

        data.forEach(row => {
            if (row.nama || row.tanggal_pickup) {
                // Gunakan nilai yang sudah ada di row, jangan hitung ulang dari rumus mentah
                totalRevenue += parseFloat(row.penjualan) || 0;
                totalCost += parseFloat(row.total_biaya) || 0;
                totalProfit += parseFloat(row.profit) || 0;
                count++;
            }
        });

        return {
            totalRevenue,
            totalCost,
            totalProfit,
            totalShipments: count
        };
    }

    // Helper formatting yang sekarang didelegasikan ke window.Formatter
    formatCurrency(amount) {
        return window.Formatter ? window.Formatter.currency(amount) : amount;
    }

    formatPercentage(value) {
        return window.Formatter ? window.Formatter.percent(value) : `${value}%`;
    }
}

window.calculationsManager = new CalculationsManager();