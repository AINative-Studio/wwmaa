#!/usr/bin/env node
/**
 * Accessibility Report Generator
 * Generates HTML report of accessibility violations across the application
 *
 * Usage:
 *   node scripts/generate-a11y-report.js
 *   npm run test:a11y:report
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const OUTPUT_FILE = 'a11y-report.html';
const REPORT_TITLE = 'Accessibility Test Report';
const SEVERITY_COLORS = {
  critical: '#dc2626',
  serious: '#ea580c',
  moderate: '#f59e0b',
  minor: '#3b82f6',
};

console.log('🔍 Running accessibility tests...\n');

try {
  // Run jest with JSON output
  const testOutput = execSync(
    'npm test -- __tests__/a11y --json --outputFile=test-results.json',
    { encoding: 'utf-8', stdio: 'pipe' }
  );

  console.log('✅ Tests completed\n');
} catch (error) {
  console.log('⚠️  Tests completed with violations\n');
}

// Read test results
let testResults = {};
try {
  const resultsFile = path.join(process.cwd(), 'test-results.json');
  if (fs.existsSync(resultsFile)) {
    const resultsContent = fs.readFileSync(resultsFile, 'utf-8');
    testResults = JSON.parse(resultsContent);
  }
} catch (error) {
  console.error('Error reading test results:', error.message);
}

// Parse violations from test results
const violations = parseViolations(testResults);

// Generate HTML report
const htmlReport = generateHTMLReport(violations);

// Write report to file
fs.writeFileSync(OUTPUT_FILE, htmlReport);

console.log(`📄 Report generated: ${OUTPUT_FILE}`);
console.log(`📊 Total violations: ${violations.length}`);
console.log(`   Critical: ${violations.filter(v => v.severity === 'critical').length}`);
console.log(`   Serious: ${violations.filter(v => v.severity === 'serious').length}`);
console.log(`   Moderate: ${violations.filter(v => v.severity === 'moderate').length}`);
console.log(`   Minor: ${violations.filter(v => v.severity === 'minor').length}`);

// Clean up
if (fs.existsSync('test-results.json')) {
  fs.unlinkSync('test-results.json');
}

/**
 * Parse violations from Jest test results
 */
function parseViolations(results) {
  const violations = [];

  if (!results.testResults) {
    return violations;
  }

  results.testResults.forEach(testFile => {
    testFile.assertionResults?.forEach(test => {
      if (test.failureMessages && test.failureMessages.length > 0) {
        // Parse axe violations from failure messages
        test.failureMessages.forEach(message => {
          const parsed = parseAxeViolation(message);
          if (parsed) {
            violations.push({
              ...parsed,
              component: extractComponentName(testFile.name),
              testName: test.title,
            });
          }
        });
      }
    });
  });

  return violations;
}

/**
 * Parse individual axe violation from error message
 */
function parseAxeViolation(message) {
  // This is a simplified parser - axe violations have specific format
  // In production, you might want more robust parsing

  const severityMatch = message.match(/impact:\s*(critical|serious|moderate|minor)/i);
  const ruleMatch = message.match(/id:\s*"([^"]+)"/);
  const descriptionMatch = message.match(/description:\s*"([^"]+)"/);

  if (!severityMatch) {
    return null;
  }

  return {
    severity: severityMatch[1].toLowerCase(),
    rule: ruleMatch ? ruleMatch[1] : 'unknown',
    description: descriptionMatch ? descriptionMatch[1] : 'No description available',
    wcagLevel: determineWCAGLevel(ruleMatch ? ruleMatch[1] : ''),
  };
}

/**
 * Determine WCAG level from rule ID
 */
function determineWCAGLevel(ruleId) {
  // Map common axe rule IDs to WCAG criteria
  const wcagMap = {
    'image-alt': '1.1.1 (Level A)',
    'color-contrast': '1.4.3 (Level AA)',
    'label': '3.3.2 (Level A)',
    'button-name': '4.1.2 (Level A)',
    'link-name': '4.1.2 (Level A)',
    'heading-order': '2.4.6 (Level AA)',
    'landmark-one-main': '2.4.1 (Level A)',
  };

  return wcagMap[ruleId] || 'Unknown';
}

/**
 * Extract component name from file path
 */
function extractComponentName(filePath) {
  const match = filePath.match(/([^\/\\]+)\.test\.[jt]sx?$/);
  return match ? match[1] : 'Unknown Component';
}

/**
 * Generate HTML report
 */
function generateHTMLReport(violations) {
  const criticalCount = violations.filter(v => v.severity === 'critical').length;
  const seriousCount = violations.filter(v => v.severity === 'serious').length;
  const moderateCount = violations.filter(v => v.severity === 'moderate').length;
  const minorCount = violations.filter(v => v.severity === 'minor').length;
  const totalCount = violations.length;

  const passRate = totalCount === 0 ? 100 : Math.max(0, 100 - (totalCount * 2));
  const grade = getGrade(criticalCount, seriousCount, moderateCount, minorCount);

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${REPORT_TITLE}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      color: #1f2937;
      background: #f9fafb;
      padding: 2rem;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      overflow: hidden;
    }
    header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 2rem;
      text-align: center;
    }
    h1 {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }
    .subtitle {
      opacity: 0.9;
      font-size: 1rem;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.5rem;
      padding: 2rem;
      background: #f9fafb;
    }
    .stat {
      background: white;
      padding: 1.5rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      text-align: center;
    }
    .stat-value {
      font-size: 2.5rem;
      font-weight: bold;
      margin-bottom: 0.5rem;
    }
    .stat-label {
      color: #6b7280;
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .grade {
      font-size: 3rem !important;
      color: ${grade.color};
    }
    .violations {
      padding: 2rem;
    }
    .violation {
      border: 1px solid #e5e7eb;
      border-left: 4px solid;
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      background: white;
    }
    .violation.critical { border-left-color: ${SEVERITY_COLORS.critical}; }
    .violation.serious { border-left-color: ${SEVERITY_COLORS.serious}; }
    .violation.moderate { border-left-color: ${SEVERITY_COLORS.moderate}; }
    .violation.minor { border-left-color: ${SEVERITY_COLORS.minor}; }
    .violation-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1rem;
    }
    .severity-badge {
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      color: white;
    }
    .severity-badge.critical { background: ${SEVERITY_COLORS.critical}; }
    .severity-badge.serious { background: ${SEVERITY_COLORS.serious}; }
    .severity-badge.moderate { background: ${SEVERITY_COLORS.moderate}; }
    .severity-badge.minor { background: ${SEVERITY_COLORS.minor}; }
    .violation-title {
      font-size: 1.125rem;
      font-weight: 600;
      flex: 1;
    }
    .violation-meta {
      display: flex;
      gap: 2rem;
      margin-bottom: 1rem;
      font-size: 0.875rem;
      color: #6b7280;
    }
    .violation-meta span {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .violation-description {
      color: #4b5563;
      line-height: 1.6;
    }
    .no-violations {
      text-align: center;
      padding: 4rem 2rem;
      color: #10b981;
    }
    .no-violations svg {
      width: 4rem;
      height: 4rem;
      margin-bottom: 1rem;
    }
    .no-violations h2 {
      font-size: 1.5rem;
      margin-bottom: 0.5rem;
    }
    footer {
      background: #f9fafb;
      padding: 1.5rem 2rem;
      text-align: center;
      color: #6b7280;
      font-size: 0.875rem;
      border-top: 1px solid #e5e7eb;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>${REPORT_TITLE}</h1>
      <p class="subtitle">Generated on ${new Date().toLocaleString()}</p>
    </header>

    <div class="summary">
      <div class="stat">
        <div class="stat-value grade">${grade.letter}</div>
        <div class="stat-label">Overall Grade</div>
      </div>
      <div class="stat">
        <div class="stat-value">${totalCount}</div>
        <div class="stat-label">Total Violations</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color: ${SEVERITY_COLORS.critical}">${criticalCount}</div>
        <div class="stat-label">Critical</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color: ${SEVERITY_COLORS.serious}">${seriousCount}</div>
        <div class="stat-label">Serious</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color: ${SEVERITY_COLORS.moderate}">${moderateCount}</div>
        <div class="stat-label">Moderate</div>
      </div>
      <div class="stat">
        <div class="stat-value" style="color: ${SEVERITY_COLORS.minor}">${minorCount}</div>
        <div class="stat-label">Minor</div>
      </div>
    </div>

    <div class="violations">
      ${violations.length === 0 ? `
        <div class="no-violations">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <h2>No Violations Found!</h2>
          <p>All accessibility tests passed. Great work!</p>
        </div>
      ` : violations.map(v => `
        <div class="violation ${v.severity}">
          <div class="violation-header">
            <span class="severity-badge ${v.severity}">${v.severity}</span>
            <span class="violation-title">${v.rule}</span>
          </div>
          <div class="violation-meta">
            <span>📋 Component: ${v.component}</span>
            <span>📏 WCAG: ${v.wcagLevel}</span>
          </div>
          <div class="violation-description">
            ${v.description}
          </div>
        </div>
      `).join('')}
    </div>

    <footer>
      <p>Generated by World Wide Martial Arts Alliance Accessibility Testing Suite</p>
      <p>Powered by jest-axe and axe-core</p>
    </footer>
  </div>
</body>
</html>
  `.trim();
}

/**
 * Determine overall grade based on violations
 */
function getGrade(critical, serious, moderate, minor) {
  if (critical > 0) {
    return { letter: 'F', color: '#dc2626' };
  }
  if (serious > 0) {
    return { letter: 'D', color: '#ea580c' };
  }
  if (moderate > 5) {
    return { letter: 'C', color: '#f59e0b' };
  }
  if (moderate > 0 || minor > 10) {
    return { letter: 'B', color: '#3b82f6' };
  }
  return { letter: 'A', color: '#10b981' };
}

console.log('\n✅ Report generation complete!\n');
