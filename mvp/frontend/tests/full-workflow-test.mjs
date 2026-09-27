/**
 * Full Workflow Integration Test
 * Tests complete user journey from dataset to experiment creation
 */

const BASE_URL = 'https://dung-ununited-seriately.ngrok-free.dev/api';

const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m'
};

function log(color, ...args) {
  console.log(color, ...args, colors.reset);
}

async function testAPI(name, method, path, body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true'
    }
  };
  
  if (body) options.body = JSON.stringify(body);
  
  try {
    log(colors.cyan, `\n🔍 ${name}`);
    const response = await fetch(`${BASE_URL}${path}`, options);
    const data = await response.json();
    
    if (response.ok) {
      log(colors.green, `   ✅ SUCCESS - Status: ${response.status}`);
      return { success: true, data, status: response.status };
    } else {
      log(colors.red, `   ❌ FAILED - Status: ${response.status}`);
      console.log('   Response:', JSON.stringify(data, null, 2));
      return { success: false, data, status: response.status };
    }
  } catch (error) {
    log(colors.red, `   ❌ ERROR: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function runFullWorkflow() {
  log(colors.blue, '\n' + '='.repeat(70));
  log(colors.blue, '🚀 FULL WORKFLOW INTEGRATION TEST');
  log(colors.blue, '='.repeat(70));
  log(colors.yellow, `Backend: ${BASE_URL}\n`);
  
  let testDatasetId = null;
  let testExperimentId = null;
  
  // Step 1: Get datasets
  log(colors.yellow, '\n📦 STEP 1: Fetch Available Datasets');
  const datasets = await testAPI('GET Datasets', 'GET', '/datasets');
  
  if (datasets.success && datasets.data.datasets?.length > 0) {
    testDatasetId = datasets.data.datasets[0].dataset_id;
    log(colors.green, `   📌 Using dataset: ${testDatasetId}`);
    log(colors.cyan, `   📋 Dataset: ${datasets.data.datasets[0].filename}`);
    log(colors.cyan, `   📊 Total datasets: ${datasets.data.datasets.length}`);
  } else {
    log(colors.red, '   ⚠️  No datasets available. Upload a dataset first!');
    return;
  }
  
  // Step 2: Get dataset details
  log(colors.yellow, '\n📦 STEP 2: Get Dataset Profile');
  const datasetDetail = await testAPI(
    'GET Dataset Details',
    'GET',
    `/datasets/${testDatasetId}`
  );
  
  if (datasetDetail.success) {
    const d = datasetDetail.data;
    log(colors.cyan, `   📋 Filename: ${d.filename}`);
    log(colors.cyan, `   📊 Rows: ${d.rows || 'N/A'}`);
    log(colors.cyan, `   📊 Columns: ${d.columns || 'N/A'}`);
  }
  
  // Step 3: Create experiment
  log(colors.yellow, '\n🧪 STEP 3: Create New Experiment');
  
  const experimentPayload = {
    dataset_id: testDatasetId,
    dataset_path: `data/demo/breast_cancer.csv`, // Adjust based on your data
    n_components: 4,
    random_state: 42,
    quantum_enabled: true,
    dev_mode: true
  };
  
  log(colors.cyan, '   📤 Payload:');
  console.log('   ', JSON.stringify(experimentPayload, null, 2));
  
  const createExp = await testAPI(
    'POST Create Experiment',
    'POST',
    '/experiments',
    experimentPayload
  );
  
  if (createExp.success) {
    testExperimentId = createExp.data.experiment_id;
    log(colors.green, `   🎯 Experiment Created: ${testExperimentId}`);
    log(colors.cyan, `   📋 Status: ${createExp.data.status}`);
    log(colors.cyan, `   💬 Message: ${createExp.data.message}`);
  } else {
    log(colors.red, '   ⚠️  Failed to create experiment');
    if (createExp.data?.detail) {
      log(colors.red, '   Error details:');
      console.log('   ', JSON.stringify(createExp.data.detail, null, 2));
    }
    return;
  }
  
  // Step 4: Run experiment
  log(colors.yellow, '\n▶️  STEP 4: Start Experiment Execution');
  const runExp = await testAPI(
    'POST Run Experiment',
    'POST',
    `/experiments/${testExperimentId}/run`
  );
  
  if (runExp.success) {
    log(colors.green, '   ✅ Experiment execution started!');
    log(colors.cyan, `   📋 Status: ${runExp.data.status}`);
  }
  
  // Step 5: Check status
  log(colors.yellow, '\n📊 STEP 5: Check Experiment Status');
  const status = await testAPI(
    'GET Status',
    'GET',
    `/experiments/${testExperimentId}/status`
  );
  
  if (status.success) {
    log(colors.cyan, `   📋 Status: ${status.data.status}`);
    log(colors.cyan, `   🎯 Stage: ${status.data.stage || 'N/A'}`);
    log(colors.cyan, `   📈 Progress: ${(status.data.progress * 100).toFixed(1)}%`);
    log(colors.cyan, `   💬 Message: ${status.data.message || 'N/A'}`);
  }
  
  // Step 6: List all experiments
  log(colors.yellow, '\n📋 STEP 6: List All Experiments');
  const listExp = await testAPI('GET Experiments List', 'GET', '/experiments');
  
  if (listExp.success) {
    const experiments = listExp.data.experiments || listExp.data || [];
    log(colors.green, `   ✅ Found ${experiments.length} experiments`);
    
    if (experiments.length > 0) {
      log(colors.cyan, '\n   Recent experiments:');
      experiments.slice(0, 3).forEach(exp => {
        log(colors.cyan, `   - ${exp.experiment_id || exp.id}: ${exp.status || 'N/A'}`);
      });
    }
  }
  
  // Summary
  log(colors.blue, '\n' + '='.repeat(70));
  log(colors.blue, '📊 TEST SUMMARY');
  log(colors.blue, '='.repeat(70));
  
  const results = [
    { name: 'Get Datasets', success: datasets.success },
    { name: 'Get Dataset Details', success: datasetDetail.success },
    { name: 'Create Experiment', success: createExp.success },
    { name: 'Run Experiment', success: runExp.success },
    { name: 'Check Status', success: status.success },
    { name: 'List Experiments', success: listExp.success }
  ];
  
  const passed = results.filter(r => r.success).length;
  const total = results.length;
  
  results.forEach(r => {
    log(r.success ? colors.green : colors.red, `${r.success ? '✅' : '❌'} ${r.name}`);
  });
  
  log(colors.yellow, `\n📊 Success Rate: ${passed}/${total} (${((passed/total)*100).toFixed(1)}%)`);
  
  if (passed === total) {
    log(colors.green, '\n🎉 ALL TESTS PASSED! Full workflow working!\n');
  } else {
    log(colors.yellow, '\n⚠️  Some tests failed. Check details above.\n');
  }
  
  // Next steps
  log(colors.blue, '📝 NEXT STEPS FOR FRONTEND:');
  log(colors.cyan, '1. Open http://localhost:5173/');
  log(colors.cyan, '2. Navigate to Datasets page');
  log(colors.cyan, '3. Click on a dataset');
  log(colors.cyan, '4. Click "Create Experiment" button');
  log(colors.cyan, '5. Fill form and submit');
  log(colors.cyan, '6. Watch experiment run!');
  log(colors.cyan, '\n');
}

// Run the test
runFullWorkflow().catch(console.error);
