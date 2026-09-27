/**
 * Backend Integration Test Suite
 * Tests all endpoints with ngrok backend
 * Run: node tests/backend-integration.test.mjs
 */

const BASE_URL = 'https://dung-ununited-seriately.ngrok-free.dev/api';

const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(color, ...args) {
  console.log(color, ...args, colors.reset);
}

async function testEndpoint(name, method, path, body = null, expectedStatus = 200) {
  try {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true'
      }
    };
    
    if (body) {
      options.body = JSON.stringify(body);
    }
    
    log(colors.blue, `\n🔍 Testing: ${name}`);
    log(colors.yellow, `   ${method} ${path}`);
    
    const response = await fetch(`${BASE_URL}${path}`, options);
    const data = await response.json();
    
    if (response.status === expectedStatus) {
      log(colors.green, `   ✅ PASS - Status: ${response.status}`);
      console.log('   📦 Response:', JSON.stringify(data, null, 2).substring(0, 200) + '...');
      return { success: true, data, status: response.status };
    } else {
      log(colors.red, `   ❌ FAIL - Expected ${expectedStatus}, got ${response.status}`);
      console.log('   📦 Response:', data);
      return { success: false, data, status: response.status };
    }
  } catch (error) {
    log(colors.red, `   ❌ ERROR: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function runTests() {
  log(colors.blue, '\n' + '='.repeat(60));
  log(colors.blue, 'Backend Integration Test Suite');
  log(colors.blue, '='.repeat(60));
  log(colors.yellow, `Base URL: ${BASE_URL}\n`);
  
  const results = {
    total: 0,
    passed: 0,
    failed: 0
  };
  
  // Test 1: Health Check
  results.total++;
  const health = await testEndpoint(
    'Health Check',
    'GET',
    '/health'
  );
  if (health.success) results.passed++; else results.failed++;
  
  // Test 2: Config
  results.total++;
  const config = await testEndpoint(
    'Platform Config',
    'GET',
    '/config'
  );
  if (config.success) results.passed++; else results.failed++;
  
  // Test 3: List Datasets
  results.total++;
  const datasets = await testEndpoint(
    'List Datasets',
    'GET',
    '/datasets'
  );
  if (datasets.success) results.passed++; else results.failed++;
  
  let testDatasetId = null;
  let testExperimentId = null;
  
  // Get first dataset ID if available
  if (datasets.success && datasets.data.datasets && datasets.data.datasets.length > 0) {
    testDatasetId = datasets.data.datasets[0].dataset_id || datasets.data.datasets[0].id;
    log(colors.green, `   📌 Using dataset ID: ${testDatasetId}`);
    
    // Test 4: Get Dataset Details
    if (testDatasetId) {
      results.total++;
      const datasetDetail = await testEndpoint(
        'Get Dataset Details',
        'GET',
        `/datasets/${testDatasetId}`
      );
      if (datasetDetail.success) results.passed++; else results.failed++;
    }
  }
  
  // Test 5: List Experiments
  results.total++;
  const experiments = await testEndpoint(
    'List Experiments',
    'GET',
    '/experiments'
  );
  if (experiments.success) results.passed++; else results.failed++;
  
  // Get first experiment ID if available
  if (experiments.success && experiments.data) {
    const expList = Array.isArray(experiments.data) ? experiments.data : experiments.data.experiments;
    if (expList && expList.length > 0) {
      testExperimentId = expList[0].experiment_id || expList[0].id;
      log(colors.green, `   📌 Using experiment ID: ${testExperimentId}`);
      
      // Test 6: Get Experiment Status
      if (testExperimentId) {
        results.total++;
        const status = await testEndpoint(
          'Get Experiment Status',
          'GET',
          `/experiments/${testExperimentId}/status`
        );
        if (status.success) results.passed++; else results.failed++;
        
        // Test 7: Get Experiment Results (if completed)
        if (status.success && (status.data.status === 'COMPLETED' || status.data.status === 'completed')) {
          results.total++;
          const resultsData = await testEndpoint(
            'Get Experiment Results',
            'GET',
            `/experiments/${testExperimentId}/results`
          );
          if (resultsData.success) results.passed++; else results.failed++;
          
          // Test 8: Get Recommendation
          results.total++;
          const recommendation = await testEndpoint(
            'Get Quantum Recommendation',
            'GET',
            `/experiments/${testExperimentId}/recommendation`
          );
          if (recommendation.success) results.passed++; else results.failed++;
          
          // Test 9: Get Explanation
          results.total++;
          const explanation = await testEndpoint(
            'Get SHAP Explanation',
            'GET',
            `/experiments/${testExperimentId}/explanation`
          );
          if (explanation.success) results.passed++; else results.failed++;
          
          // Test 10: Get Resources
          results.total++;
          const resources = await testEndpoint(
            'Get Resource Usage',
            'GET',
            `/experiments/${testExperimentId}/resources`
          );
          if (resources.success) results.passed++; else results.failed++;
          
          // Test 11: Get Confusion Matrix
          results.total++;
          const confusion = await testEndpoint(
            'Get Confusion Matrix (VQC)',
            'GET',
            `/experiments/${testExperimentId}/confusion-matrix/VQC`
          );
          if (confusion.success) results.passed++; else results.failed++;
          
          // Test 12: Predict (if model available)
          if (resultsData.success && resultsData.data.results && resultsData.data.results.models) {
            const modelName = Object.keys(resultsData.data.results.models)[0];
            results.total++;
            const predict = await testEndpoint(
              'Predict Patient Risk',
              'POST',
              `/experiments/${testExperimentId}/predict`,
              {
                features: [17.99, 10.38, 122.8, 1001.0, 0.1184, 0.2776, 0.3001, 0.1471],
                decision_threshold: 0.5,
                model_name: modelName
              }
            );
            if (predict.success) results.passed++; else results.failed++;
          }
        }
      }
    }
  }
  
  // Test 13: Create Experiment (if we have a dataset)
  if (testDatasetId) {
    results.total++;
    const createExp = await testEndpoint(
      'Create New Experiment',
      'POST',
      '/experiments',
      {
        dataset_id: testDatasetId,
        n_components: 4,
        random_state: 42,
        quantum_enabled: true,
        dev_mode: true
      },
      201
    );
    if (createExp.success) {
      results.passed++;
      const newExpId = createExp.data.experiment_id;
      log(colors.green, `   📌 Created experiment: ${newExpId}`);
      
      // Test 14: Run Experiment
      results.total++;
      const runExp = await testEndpoint(
        'Run Experiment',
        'POST',
        `/experiments/${newExpId}/run`,
        null,
        202
      );
      if (runExp.success) results.passed++; else results.failed++;
    } else {
      results.failed++;
    }
  }
  
  // Summary
  log(colors.blue, '\n' + '='.repeat(60));
  log(colors.blue, 'Test Summary');
  log(colors.blue, '='.repeat(60));
  log(colors.yellow, `Total Tests: ${results.total}`);
  log(colors.green, `Passed: ${results.passed}`);
  log(colors.red, `Failed: ${results.failed}`);
  log(colors.yellow, `Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`);
  log(colors.blue, '='.repeat(60) + '\n');
  
  if (results.failed === 0) {
    log(colors.green, '🎉 All tests passed! Backend integration is working perfectly!\n');
  } else {
    log(colors.red, '⚠️  Some tests failed. Check the output above for details.\n');
  }
}

// Run tests
runTests().catch(console.error);
