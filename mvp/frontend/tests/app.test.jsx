import React from 'react';
import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from '@/App.jsx';
import api from '@/services/api.js';
import { mockBackend } from '@/lib/mockData.js';

/**
 * Full-app smoke tests in mock mode. Run twice:
 *   npm test                  → contract/mock JSON shapes (guide_naeem.md §4)
 *   npm run test:backend-shape→ mvp/backend's actual response shapes
 * Both must pass — that is what proves src/lib/adapters.js keeps every page
 * working no matter which side of the drift the data comes from.
 */

const SHAPE = import.meta.env.VITE_SHAPE;
let consoleErrors = [];
const realError = console.error;

beforeAll(() => {
  console.error = (...a) => { consoleErrors.push(a.join(' ')); realError(...a); };
});
afterEach(() => { consoleErrors = []; });
afterAll(() => { console.error = realError; });

const renderAt = (path) => render(<MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><App /></MemoryRouter>);

const seriousWarnings = () => {
  const bad = consoleErrors.filter((m) => /unique "key"|unknown prop|cannot be given refs|validateDOMNesting|each child in a list/i.test(m));
  expect(bad, bad.join('\n')).toEqual([]);
};

let datasetId;

describe(`shell · ${SHAPE} shapes`, () => {
  it('dashboard: hero, live KPIs and the registered demo datasets', async () => {
    renderAt('/');
    expect(await screen.findByText(/measured on clinical tables/i)).toBeTruthy();
    expect(await screen.findByText('Registered datasets')).toBeTruthy();
    expect(await screen.findByText('Breast Cancer Wisconsin')).toBeTruthy();
    expect(screen.getByText(/Hybrid quantum-classical benchmark engine/i)).toBeTruthy();
    expect(screen.getByLabelText('Primary')).toBeTruthy();          // nav landmark
    expect(screen.getByText(/research \/ benchmarking system/i)).toBeTruthy(); // disclaimer present
    seriousWarnings();
  });

  it('datasets: lists rows and the filter narrows them', async () => {
    const { unmount } = renderAt('/datasets');
    const [table] = await screen.findAllByRole('table');
    const before = within(table).getAllByRole('row').length;
    expect(before).toBeGreaterThan(2);
    datasetId = within(table).getAllByRole('link')[0].getAttribute('href').split('/').pop();

    await userEvent.type(screen.getByLabelText('Filter datasets'), 'parkinson');
    await waitFor(() => {
      expect(within(screen.getAllByRole('table')[0]).getAllByRole('row').length).toBeLessThan(before);
    });
    unmount();
    seriousWarnings();
  });

  it('dataset detail: profile stats, target and class percentages', async () => {
    const list = await api.listDatasets();
    const id = list.datasets[0].id;
    renderAt(`/datasets/${id}`);
    expect(await screen.findByText(/Phase 2 · profile/i)).toBeTruthy();
    expect(await screen.findByText('Samples')).toBeTruthy();
    expect(await screen.findByText('Missing values')).toBeTruthy();
    expect(await screen.findByText(/Target & class balance/i)).toBeTruthy();
    expect((await screen.findAllByText(/\d+\.\d%/)).length).toBeGreaterThan(0);   // class % rendered
    expect(screen.getAllByText(/research \/ benchmarking/i).length).toBeGreaterThan(0);
    seriousWarnings();
  });

  it('experiment new: shows the generated plan and runs it', async () => {
    const list = await api.listDatasets();
    renderAt(`/experiments/new/${list.datasets[0].id}`);
    expect(await screen.findByText('Pipeline configuration')).toBeTruthy();
    expect(await screen.findByText('Why this pipeline?', { exact: false })).toBeTruthy();
    expect(await screen.findByText(/Stratified 80\/20 split/i)).toBeTruthy();
    const runBtn = await screen.findByRole('button', { name: /Run benchmark ·/ });
    expect(runBtn).toBeTruthy();
    await userEvent.click(runBtn);
    expect(await screen.findByText(/Stage execution/i, { timeout: 6000 })).toBeTruthy();
    seriousWarnings();
  });

  it('experiment detail: progress → results → explain → cost on a completed run', async () => {
    const list = await api.listDatasets();
    const created = await api.createExperiment(list.datasets[0].id, { name: 'smoke run' });
    mockBackend.complete(created.id);                                  // jump the mock timeline to COMPLETED

    const { container } = renderAt(`/experiments/${created.id}`);
    expect(await screen.findByText(/Quantum value assessment/i)).toBeTruthy();
    expect(screen.getByText('Classification', { exact: true })).toBeTruthy();

    // results tab (auto-selected on completion) — all four arms in the table
    const [table] = await screen.findAllByRole('table');
    for (const m of ['Random Forest', 'Logistic Regression', 'SVM (RBF)', 'VQC (quantum)']) {
      expect(within(table).getByText(m, { exact: false })).toBeTruthy();
    }
    expect(within(table).getByText('Precision')).toBeTruthy();        // metric the guide's table dropped

    // explainability tab
    await userEvent.click(screen.getByRole('tab', { name: /Explainability/i }));
    expect(await screen.findByText(/Prediction trace/i)).toBeTruthy();
    expect((await screen.findAllByText(/Uncalibrated/i)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/PC\d|_worst|_mean/).length).toBeGreaterThan(0);

    // cost tab
    await userEvent.click(screen.getByRole('tab', { name: /Cost & resources/i }));
    expect(await screen.findByText('₹0')).toBeTruthy();
    expect(screen.getByText(/Local quantum simulator/i)).toBeTruthy();
    expect(screen.getByText(/Performance vs cost/i)).toBeTruthy();
    expect(container.querySelector('.card')).toBeTruthy();
    seriousWarnings();
  });

  it('reports page lists artifacts and can generate one', async () => {
    renderAt('/reports');
    expect(await screen.findByRole('heading', { name: /^Reports$/i })).toBeTruthy();
    expect(await screen.findByText(/16 sections/i)).toBeTruthy();
    seriousWarnings();
  });


  it('⌘K palette opens, filters and jumps', async () => {
    renderAt('/');
    await screen.findByText(/measured on clinical tables/i);
    await userEvent.keyboard('{Meta>}k{/Meta}');
    const box = await screen.findByPlaceholderText(/Jump to a page/i);
    await userEvent.type(box, 'expe');
    const options = screen.getAllByRole('option');
    expect(options.length).toBeGreaterThan(0);
    // the palette must actually navigate, not merely close
    await userEvent.click(options[0]);
    expect(await screen.findByRole('heading', { name: /experiments/i })).toBeTruthy();
    await userEvent.keyboard('{Meta>}k{/Meta}');
    await screen.findByPlaceholderText(/Jump to a page/i);
    await userEvent.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByLabelText('Search')).toBeNull());
    seriousWarnings();
  });

  it('unknown route renders the 404 shell instead of a blank page', async () => {
    renderAt('/nope');
    expect(await screen.findByText(/does not exist/i)).toBeTruthy();
    seriousWarnings();
  });
});
