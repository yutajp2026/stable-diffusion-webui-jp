import base64
import io
import time

import gradio as gr
from pydantic import BaseModel, Field

from modules.shared import opts

import modules.shared as shared
from collections import OrderedDict
import string
import random
from typing import List

current_task = None
pending_tasks = OrderedDict()
finished_tasks = []
recorded_results = []
recorded_results_limit = 2


def start_task(id_task):
    global current_task

    current_task = id_task
    pending_tasks.pop(id_task, None)


def finish_task(id_task):
    global current_task

    if current_task == id_task:
        current_task = None

    finished_tasks.append(id_task)
    if len(finished_tasks) > 16:
        finished_tasks.pop(0)

def create_task_id(task_type):
    N = 7
    res = ''.join(random.choices(string.ascii_uppercase +
    string.digits, k=N))
    return f"task({task_type}-{res})"

def record_results(id_task, res):
    recorded_results.append((id_task, res))
    if len(recorded_results) > recorded_results_limit:
        recorded_results.pop(0)


def add_task_to_queue(id_job):
    pending_tasks[id_job] = time.time()

class PendingTasksResponse(BaseModel):
    size: int = Field(title="保留中のタスクのサイズ")
    tasks: List[str] = Field(title="保留中のタスクID")

class ProgressRequest(BaseModel):
    id_task: str = Field(default=None, title="タスクID", description="進行状況を取得するタスクのID")
    id_live_preview: int = Field(default=-1, title="ライブプレビューイメージID", description="最後に受信したプレビューイメージのID")
    live_preview: bool = Field(default=True, title="ライブプレビューを含める", description="ライブプレビューイメージを含めるかどうかを示すブールフラグ")


class ProgressResponse(BaseModel):
    active: bool = Field(title="保留中のタスクかどうか")
    queued: bool = Field(title="タスクがキュー内にあるかどうか")
    completed: bool = Field(title="タスクが完了したかどうか")
    progress: float = Field(default=None, title="進行状況", description="0から1までの範囲の進行状況")
    eta: float = Field(default=None, title="残り時間（秒）")
    live_preview: str = Field(default=None, title="ライブプレビューイメージ", description="現在のライブプレビュー: data: uri")
    id_live_preview: int = Field(default=None, title="ライブプレビューイメージID", description="次のリクエストと一緒に送信して、同じイメージを受信しないようにする")
    textinfo: str = Field(default=None, title="情報テキスト", description="WebUIで使用される情報テキスト。")


def setup_progress_api(app):
    app.add_api_route("/internal/pending-tasks", get_pending_tasks, methods=["GET"])
    return app.add_api_route("/internal/progress", progressapi, methods=["POST"], response_model=ProgressResponse)


def get_pending_tasks():
    pending_tasks_ids = list(pending_tasks)
    pending_len = len(pending_tasks_ids)
    return PendingTasksResponse(size=pending_len, tasks=pending_tasks_ids)


def progressapi(req: ProgressRequest):
    active = req.id_task == current_task
    queued = req.id_task in pending_tasks
    completed = req.id_task in finished_tasks

    if not active:
        textinfo = "待機中..."
        if queued:
            sorted_queued = sorted(pending_tasks.keys(), key=lambda x: pending_tasks[x])
            queue_index = sorted_queued.index(req.id_task)
            textinfo = "キュー内: {}/{}".format(queue_index + 1, len(sorted_queued))
        return ProgressResponse(active=active, queued=queued, completed=completed, id_live_preview=-1, textinfo=textinfo)

    progress = 0

    job_count, job_no = shared.state.job_count, shared.state.job_no
    sampling_steps, sampling_step = shared.state.sampling_steps, shared.state.sampling_step

    if job_count > 0:
        progress += job_no / job_count
    if sampling_steps > 0 and job_count > 0:
        progress += 1 / job_count * sampling_step / sampling_steps

    progress = min(progress, 1)

    elapsed_since_start = time.time() - shared.state.time_start
    predicted_duration = elapsed_since_start / progress if progress > 0 else None
    eta = predicted_duration - elapsed_since_start if predicted_duration is not None else None

    live_preview = None
    id_live_preview = req.id_live_preview

    if opts.live_previews_enable and req.live_preview:
        shared.state.set_current_image()
        if shared.state.id_live_preview != req.id_live_preview:
            image = shared.state.current_image
            if image is not None:
                buffered = io.BytesIO()

                if opts.live_previews_image_format == "png":
                    # using optimize for large images takes an enormous amount of time
                    if max(*image.size) <= 256:
                        save_kwargs = {"optimize": True}
                    else:
                        save_kwargs = {"optimize": False, "compress_level": 1}

                else:
                    save_kwargs = {}

                image.save(buffered, format=opts.live_previews_image_format, **save_kwargs)
                base64_image = base64.b64encode(buffered.getvalue()).decode('ascii')
                live_preview = f"data:image/{opts.live_previews_image_format};base64,{base64_image}"
                id_live_preview = shared.state.id_live_preview

    return ProgressResponse(active=active, queued=queued, completed=completed, progress=progress, eta=eta, live_preview=live_preview, id_live_preview=id_live_preview, textinfo=shared.state.textinfo)


def restore_progress(id_task):
    while id_task == current_task or id_task in pending_tasks:
        time.sleep(0.1)

    res = next(iter([x[1] for x in recorded_results if id_task == x[0]]), None)
    if res is not None:
        return res

    return gr.update(), gr.update(), gr.update(), f"{id_task} の進行状況を復元できませんでした：結果は破棄されたか、あるいはそもそも取得されていませんでした。"
