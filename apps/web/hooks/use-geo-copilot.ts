"use client";

import { useCallback, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import {
  createAnalysis,
  createUploadedAnalysis,
  clearProviderConfig,
  generateDiagnosis,
  getDiagnosis,
  getMessages,
  getMethods,
  getProviderConfig,
  getStrategy,
  sendMessage,
  setProviderConfig,
  testProviderConfig,
} from "../lib/api-client";
import { toUserMessage } from "../lib/format";
import type {
  AnalysisCreateInput,
  ConversationMessageRequest,
  ProviderConfigInput,
  ProviderConfigPublic,
  ProviderTestResponse,
  UploadedAnalysisInput,
  WorkbenchData,
} from "../types/api";

export type WorkbenchStatus = "idle" | "loading" | "ready" | "failed";

export type WorkbenchState = WorkbenchData & {
  status: WorkbenchStatus;
  operations: {
    creatingAnalysis: boolean;
    loadingReadModels: boolean;
    loadingDiagnosis: boolean;
    generatingDiagnosis: boolean;
    sendingMessage: boolean;
    savingProvider: boolean;
    testingProvider: boolean;
  };
  error: string | null;
  providerConfig: ProviderConfigPublic | null;
  providerTest: ProviderTestResponse | null;
  readModelErrors: {
    methods: string | null;
    strategy: string | null;
    diagnosis: string | null;
    history: string | null;
  };
};

const INITIAL_STATE: WorkbenchState = {
  status: "idle",
  operations: {
    creatingAnalysis: false,
    loadingReadModels: false,
    loadingDiagnosis: false,
    generatingDiagnosis: false,
    sendingMessage: false,
    savingProvider: false,
    testingProvider: false,
  },
  error: null,
  providerConfig: null,
  providerTest: null,
  readModelErrors: {
    methods: null,
    strategy: null,
    diagnosis: null,
    history: null,
  },
  analysis: null,
  methods: null,
  strategy: null,
  diagnosis: null,
  history: null,
};

export function useGeoCopilot() {
  const [state, setState] = useState<WorkbenchState>(INITIAL_STATE);

  const currentAnalysisId = state.analysis?.id ?? null;

  const submitUrlAnalysis = useCallback(async (input: AnalysisCreateInput) => {
    setState({
      ...INITIAL_STATE,
      status: "loading",
      operations: { ...INITIAL_STATE.operations, creatingAnalysis: true },
    });
    try {
      const analysis = await createAnalysis(input);
      setState((current) => ({
        ...current,
        status: "ready",
        operations: { ...current.operations, creatingAnalysis: false },
        analysis,
      }));
      if (analysis.status === "completed") {
        await loadReadModels(analysis.id, setState);
      }
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "failed",
        operations: { ...current.operations, creatingAnalysis: false },
        error: toUserMessage(error),
      }));
    }
  }, []);

  const submitUploadedAnalysis = useCallback(async (input: UploadedAnalysisInput) => {
    setState({
      ...INITIAL_STATE,
      status: "loading",
      operations: { ...INITIAL_STATE.operations, creatingAnalysis: true },
    });
    try {
      const analysis = await createUploadedAnalysis(input);
      setState((current) => ({
        ...current,
        status: "ready",
        operations: { ...current.operations, creatingAnalysis: false },
        analysis,
      }));
      if (analysis.status === "completed") {
        await loadReadModels(analysis.id, setState);
      }
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "failed",
        operations: { ...current.operations, creatingAnalysis: false },
        error: toUserMessage(error),
      }));
    }
  }, []);

  const refreshDiagnosis = useCallback(async () => {
    if (!currentAnalysisId) {
      return;
    }
    setState((current) => ({
      ...current,
      operations: { ...current.operations, loadingDiagnosis: true },
      readModelErrors: { ...current.readModelErrors, diagnosis: null },
    }));
    try {
      const diagnosis = await getDiagnosis(currentAnalysisId);
      setState((current) => ({
        ...current,
        operations: { ...current.operations, loadingDiagnosis: false },
        diagnosis,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        operations: { ...current.operations, loadingDiagnosis: false },
        readModelErrors: { ...current.readModelErrors, diagnosis: toUserMessage(error) },
      }));
    }
  }, [currentAnalysisId]);

  const createDiagnosis = useCallback(async () => {
    if (!currentAnalysisId) {
      return;
    }
    setState((current) => ({
      ...current,
      operations: { ...current.operations, generatingDiagnosis: true },
      readModelErrors: { ...current.readModelErrors, diagnosis: null },
    }));
    try {
      const diagnosis = await generateDiagnosis(currentAnalysisId);
      setState((current) => ({
        ...current,
        operations: { ...current.operations, generatingDiagnosis: false },
        diagnosis,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        operations: { ...current.operations, generatingDiagnosis: false },
        readModelErrors: { ...current.readModelErrors, diagnosis: toUserMessage(error) },
      }));
    }
  }, [currentAnalysisId]);

  const postMessage = useCallback(
    async (input: ConversationMessageRequest) => {
      if (!currentAnalysisId) {
        return;
      }
      setState((current) => ({
        ...current,
        operations: { ...current.operations, sendingMessage: true },
        readModelErrors: { ...current.readModelErrors, history: null },
      }));
      try {
        await sendMessage(currentAnalysisId, input);
        const history = await getMessages(currentAnalysisId);
        setState((current) => ({
          ...current,
          operations: { ...current.operations, sendingMessage: false },
          history,
        }));
      } catch (error) {
        setState((current) => ({
          ...current,
          operations: { ...current.operations, sendingMessage: false },
          readModelErrors: { ...current.readModelErrors, history: toUserMessage(error) },
        }));
      }
    },
    [currentAnalysisId],
  );

  const saveProvider = useCallback(async (input: ProviderConfigInput) => {
    setState((current) => ({
      ...current,
      operations: { ...current.operations, savingProvider: true },
      error: null,
      providerTest: null,
    }));
    try {
      const providerConfig = await setProviderConfig(input);
      setState((current) => ({
        ...current,
        operations: { ...current.operations, savingProvider: false },
        providerConfig,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        operations: { ...current.operations, savingProvider: false },
        error: toUserMessage(error),
      }));
    }
  }, []);

  const testProvider = useCallback(async (input: ProviderConfigInput) => {
    setState((current) => ({
      ...current,
      operations: { ...current.operations, testingProvider: true },
      error: null,
      providerTest: null,
    }));
    try {
      const providerTest = await testProviderConfig(input);
      setState((current) => ({
        ...current,
        operations: { ...current.operations, testingProvider: false },
        providerTest,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        operations: { ...current.operations, testingProvider: false },
        error: toUserMessage(error),
      }));
    }
  }, []);

  const clearProvider = useCallback(async () => {
    setState((current) => ({
      ...current,
      operations: { ...current.operations, savingProvider: true },
      error: null,
      providerTest: null,
    }));
    try {
      const providerConfig = await clearProviderConfig();
      setState((current) => ({
        ...current,
        operations: { ...current.operations, savingProvider: false },
        providerConfig,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        operations: { ...current.operations, savingProvider: false },
        error: toUserMessage(error),
      }));
    }
  }, []);

  const refreshProvider = useCallback(async () => {
    try {
      const providerConfig = await getProviderConfig();
      setState((current) => ({ ...current, providerConfig }));
    } catch {
      // Provider config is useful but non-blocking for analysis UI.
    }
  }, []);

  const actions = useMemo(
    () => ({
      submitUrlAnalysis,
      submitUploadedAnalysis,
      refreshDiagnosis,
      createDiagnosis,
      postMessage,
      saveProvider,
      testProvider,
      clearProvider,
      refreshProvider,
    }),
    [
      clearProvider,
      createDiagnosis,
      postMessage,
      refreshDiagnosis,
      refreshProvider,
      saveProvider,
      submitUploadedAnalysis,
      submitUrlAnalysis,
      testProvider,
    ],
  );

  return { state, actions };
}

async function loadReadModels(
  analysisId: string,
  setState: Dispatch<SetStateAction<WorkbenchState>>,
): Promise<void> {
  setState((current) => ({
    ...current,
    operations: { ...current.operations, loadingReadModels: true },
    readModelErrors: INITIAL_STATE.readModelErrors,
  }));
  const [methodsResult, strategyResult, historyResult, diagnosisResult] = await Promise.allSettled([
    getMethods(analysisId),
    getStrategy(analysisId),
    getMessages(analysisId),
    getDiagnosis(analysisId),
  ]);

  setState((current) => ({
    ...current,
    operations: { ...current.operations, loadingReadModels: false },
    methods: methodsResult.status === "fulfilled" ? methodsResult.value : current.methods,
    strategy: strategyResult.status === "fulfilled" ? strategyResult.value : current.strategy,
    history: historyResult.status === "fulfilled" ? historyResult.value : current.history,
    diagnosis: diagnosisResult.status === "fulfilled" ? diagnosisResult.value : current.diagnosis,
    readModelErrors: {
      methods: methodsResult.status === "rejected" ? toUserMessage(methodsResult.reason) : null,
      strategy: strategyResult.status === "rejected" ? toUserMessage(strategyResult.reason) : null,
      history: historyResult.status === "rejected" ? toUserMessage(historyResult.reason) : null,
      diagnosis: diagnosisResult.status === "rejected" ? toUserMessage(diagnosisResult.reason) : null,
    },
  }));
}
