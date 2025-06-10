import Mlflow from 'mlflow-js';

/**
 * Wrapper around the mlflow-js library to make it better typed / easier to use.
 */
export default class MLFlowClient {
  private mlflow: Mlflow;

  constructor(trackingUri: string) {
    this.mlflow = new Mlflow(trackingUri);
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
  tags?: Record<string, string>;
};

export type MLFlowRunMetric = {
  key: string;
  value: number;
  timestamp: number;
  step: number;
};
