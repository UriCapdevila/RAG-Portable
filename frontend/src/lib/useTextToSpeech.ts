import { useCallback, useEffect, useRef, useState } from "react";

import { fetchTTSStatus, synthesizeSpeech } from "./api";

export type TTSPlaybackState = "idle" | "loading" | "speaking";

export type TextToSpeechController = {
  enabled: boolean;
  loadingId: string | null;
  speakingId: string | null;
  errorMessage: string | null;
  speak: (id: string, text: string) => void;
  stop: () => void;
  clearError: () => void;
  stateFor: (id: string) => TTSPlaybackState;
};

export function useTextToSpeech(): TextToSpeechController {
  const [enabled, setEnabled] = useState(true);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [speakingId, setSpeakingId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeIdRef = useRef<string | null>(null);

  const releaseAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current.pause();
      audioRef.current.removeAttribute("src");
      audioRef.current.load();
      audioRef.current = null;
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    activeIdRef.current = null;
    releaseAudio();
    setLoadingId(null);
    setSpeakingId(null);
  }, [releaseAudio]);

  useEffect(() => {
    let cancelled = false;
    fetchTTSStatus()
      .then((status) => {
        if (!cancelled) {
          setEnabled(status.enabled);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setEnabled(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      releaseAudio();
    };
  }, [releaseAudio]);

  const speak = useCallback(
    (id: string, text: string) => {
      if (!enabled) {
        return;
      }

      if (activeIdRef.current === id) {
        stop();
        return;
      }

      stop();

      const trimmed = text.trim();
      if (!trimmed) {
        return;
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;
      activeIdRef.current = id;
      setErrorMessage(null);
      setLoadingId(id);

      synthesizeSpeech(trimmed, { signal: controller.signal })
        .then((blob) => {
          if (controller.signal.aborted || activeIdRef.current !== id) {
            return;
          }

          const url = URL.createObjectURL(blob);
          objectUrlRef.current = url;

          const audio = new Audio(url);
          audioRef.current = audio;

          audio.onended = () => {
            if (activeIdRef.current === id) {
              activeIdRef.current = null;
              releaseAudio();
              setSpeakingId(null);
            }
          };
          audio.onerror = () => {
            if (activeIdRef.current === id) {
              activeIdRef.current = null;
              releaseAudio();
              setSpeakingId(null);
              setErrorMessage("No se pudo reproducir el audio.");
            }
          };

          setLoadingId((current) => (current === id ? null : current));
          setSpeakingId(id);

          void audio.play().catch((error: unknown) => {
            if (activeIdRef.current === id) {
              activeIdRef.current = null;
              releaseAudio();
              setSpeakingId(null);
              setErrorMessage(
                error instanceof Error
                  ? error.message
                  : "No se pudo iniciar la reproduccion.",
              );
            }
          });
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) {
            return;
          }
          if (activeIdRef.current === id) {
            activeIdRef.current = null;
            setLoadingId(null);
            setSpeakingId(null);
            setErrorMessage(
              error instanceof Error ? error.message : "No se pudo sintetizar la voz.",
            );
          }
        });
    },
    [enabled, releaseAudio, stop],
  );

  const clearError = useCallback(() => setErrorMessage(null), []);

  const stateFor = useCallback(
    (id: string): TTSPlaybackState => {
      if (speakingId === id) return "speaking";
      if (loadingId === id) return "loading";
      return "idle";
    },
    [loadingId, speakingId],
  );

  return {
    enabled,
    loadingId,
    speakingId,
    errorMessage,
    speak,
    stop,
    clearError,
    stateFor,
  };
}
