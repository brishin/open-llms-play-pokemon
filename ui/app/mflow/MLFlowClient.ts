import ky from 'ky';
import Mlflow from 'mlflow-js';
import type { MLFlowTraceArtifact } from './MLFlowTraces';

/**
 * Wrapper around the mlflow-js library to make it better typed / easier to use.
 */
export default class MLFlowClient {
  private mlflow: Mlflow;
  private trackingUri: string;

  constructor(trackingUri: string) {
    this.mlflow = new Mlflow(trackingUri);
    this.trackingUri = trackingUri;
  }

  async getExperiment(experimentName: string): Promise<MLFlowExperiment> {
    const experiment = await this.mlflow
      .getExperimentClient()
      .getExperimentByName(experimentName);
    return experiment as MLFlowExperiment;
  }

  async listRuns(experimentId: string): Promise<MLFlowRun[]> {
    const result = await this.mlflow.getRunClient().searchRuns(
      [experimentId],
      undefined, // filter
      undefined, // run_view_type
      undefined, // max_results
      ['attribute.end_time DESC'], // order_by
      undefined, // page_token
    );
    // @ts-expect-error Accessing object type
    return result.runs as unknown as MLFlowRun[];
  }

  async getRun(runId: string): Promise<MLFlowRun> {
    const result = await this.mlflow.getRunClient().getRun(runId);
    return result as unknown as MLFlowRun;
  }

  async getArtifacts(runId: string): Promise<unknown[]> {
    const result = (await this.mlflow
      .getRunClient()
      .listArtifacts(runId)) as MLFlowArtifactResponse;
    return result.files;
  }

  async getArtifactJSON(runId: string, artifactPath: string): Promise<unknown> {
    const url = `${this.trackingUri}/get-artifact?path=${encodeURIComponent(artifactPath)}&run_uuid=${runId}`;
    const response = await ky.get(url);
    return response.json();
  }

  async getArtifactBinary(runId: string, artifactPath: string): Promise<ArrayBuffer> {
    const url = `${this.trackingUri}/get-artifact?path=${encodeURIComponent(artifactPath)}&run_uuid=${runId}`;
    const response = await ky.get(url);
    return response.arrayBuffer();
  }

  async getTraceForRun(
    experimentId: string,
    runId: string,
  ): Promise<MLFlowTraceArtifact | undefined> {
    const traces = await this.getTraceList({
      experimentIds: [experimentId],
      orderBy: 'timestamp_ms DESC',
      sourceRun: runId,
    });
    if (traces.traces.length === 0) {
      console.error('No traces found for run', runId);
      return undefined;
    } else if (traces.traces.length > 1) {
      console.warn('Multiple traces found for run', runId);
    }
    const trace = traces.traces[0];
    return await this.getTraceArtifact(trace.request_id);
  }

  async getTraceList(options: {
    experimentIds: string[];
    orderBy?: string;
    filter?: string;
    sourceRun?: string;
  }): Promise<MLFlowTracesResponse> {
    const searchParams = new URLSearchParams();

    options.experimentIds.forEach((id) => {
      searchParams.append('experiment_ids', id);
    });

    if (options.orderBy) {
      searchParams.set('order_by', options.orderBy);
    }

    let filter = options.filter || '';
    if (options.sourceRun) {
      const sourceRunFilter = `request_metadata.\`mlflow.sourceRun\`='${options.sourceRun}'`;
      filter = filter ? `${filter} AND ${sourceRunFilter}` : sourceRunFilter;
    }

    if (filter) {
      searchParams.set('filter', filter);
    }

    const url = `${this.trackingUri}/ajax-api/2.0/mlflow/traces?${searchParams.toString()}`;
    const response = await ky.get(url);

    return response.json() as Promise<MLFlowTracesResponse>;
  }

  async getTraceArtifact(requestId: string): Promise<MLFlowTraceArtifact> {
    const url = `${this.trackingUri}/ajax-api/2.0/mlflow/get-trace-artifact?request_id=${requestId}`;
    const response = await ky.get(url);
    return response.json();
  }
}

export type MLFlowExperiment = {
  experiment_id: string;
  name: string;
  artifact_location: string;
  lifecycle_stage: string;
  last_update_time: number;
  creation_time: number;
};

export type MLFlowRun = {
  info: MLFlowRunInfo;
  data: MLFlowRunData;
};

export type MLFlowRunInfo = {
  run_id: string;
  /** @deprecated Use run_id instead */
  run_uuid: string;
  run_name: string;
  experiment_id: string;
  user_id: string;
  status: string;
  start_time: number;
  end_time: number;
  artifact_uri: string;
  lifecycle_stage: string;
};

export type MLFlowRunData = {
  metrics?: MLFlowRunMetric[];
  params?: Record<string, string>;
  tags?: { key: string; value: string }[];
};

export type MLFlowRunMetric = {
  key: string;
  value: number;
  timestamp: number;
  step: number;
};

export type MLFlowArtifactResponse = {
  root_uri: string;
  files: unknown[];
  next_page_token: string;
};

export type MLFlowTracesResponse = {
  traces: MLFlowTrace[];
  next_page_token?: string;
};

export type MLFlowTrace = {
  request_id: string;
  experiment_id: string;
  timestamp_ms: number;
  execution_time_ms: number;
  status: string;
  request_metadata: [];
  tags: { key: string; value: string }[];
};
