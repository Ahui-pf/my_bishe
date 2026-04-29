<template>
  <div class="page-stack">
    <section class="help-hero glass-panel">
      <div>
        <p class="eyebrow">Help Center</p>
        <h1 class="section-title">系统使用说明与答辩演示指南</h1>
        <p class="section-copy">
          这一页用于快速说明项目做了什么、怎么操作、演示时应该按什么顺序来讲，避免“帮助文档”入口显得空白或未完成。
        </p>
      </div>

      <div class="chip-row">
        <span class="soft-chip">Vue 前端界面</span>
        <span class="soft-chip">Flask 用户与记录管理</span>
        <span class="soft-chip">FastAPI 模型推理服务</span>
        <span class="soft-chip">WebSocket 实时检测</span>
      </div>
    </section>

    <section class="help-grid">
      <article v-for="section in sections" :key="section.title" class="section-panel help-card">
        <div class="card-index">{{ section.index }}</div>
        <h2>{{ section.title }}</h2>
        <p v-if="section.description" class="card-description">{{ section.description }}</p>
        <ul v-if="section.items.length">
          <li v-for="item in section.items" :key="item">{{ item }}</li>
        </ul>
      </article>
    </section>
  </div>
</template>

<script setup>
const sections = [
  {
    index: '01',
    title: '系统简介',
    description: '本系统基于 YOLO 模型实现路面病害智能检测，支持图片、视频与实时摄像头三种检测方式。',
    items: [
      '前端使用 Vue 构建交互界面，负责文件上传、结果展示与页面导航。',
      'Flask 服务负责用户登录、个人中心、统计信息与检测记录管理。',
      'FastAPI 服务负责模型推理、视频分析和报告生成。',
      '实时检测通过 WebSocket 传输帧数据并返回识别框结果。'
    ]
  },
  {
    index: '02',
    title: '核心功能',
    description: '项目目前已经覆盖一个完整检测平台应有的主流程。',
    items: [
      '图片检测：上传单张图片后返回识别结果与目标数量。',
      '视频检测：支持采样处理、限制处理帧数和预览检测结果。',
      '实时检测：打开摄像头后实时推理并叠加检测框。',
      '检测记录：检测成功后自动写入数据库并同步到仪表板。',
      '报告导出：可以将检测结果整理为 PDF 或 JSON 报告。'
    ]
  },
  {
    index: '03',
    title: '推荐演示顺序',
    description: '答辩时建议按下面的顺序演示，逻辑最顺、风险也最低。',
    items: [
      '先登录系统，展示首页仪表板和统计概览。',
      '进入智能检测页面，完成一次图片检测。',
      '回到仪表板查看最近活动是否已自动更新。',
      '再演示一次视频检测，突出系统支持多种输入源。',
      '最后打开实时检测，简短展示摄像头实时识别效果。',
      '在个人中心或首页导出报告，体现系统完整性。'
    ]
  },
  {
    index: '04',
    title: '参数说明',
    description: '答辩中老师如果问参数含义，可以直接按这一页解释。',
    items: [
      'conf 表示置信度阈值，值越高，保留下来的检测结果越严格。',
      'iou 表示重叠阈值，用于控制多个候选框之间的抑制强度。',
      '视频采样步长越大，处理速度越快，但可能跳过部分关键帧。',
      '视频处理帧数上限为 0 时表示自动采样，不再强制读取整段视频。',
      '实时检测帧率越高，画面更连贯，但设备压力也会更大。'
    ]
  },
  {
    index: '05',
    title: '项目优化点',
    description: '可以把这一部分当成“问题分析与改进”来讲。',
    items: [
      '针对长视频检测耗时过久的问题，加入了自动采样与有限预览返回机制。',
      '针对实时检测卡顿的问题，改为前端本地叠框并控制单帧在途。',
      '针对登录状态异常与记录保存失败的问题，统一修复了 token 传递链路。',
      '针对界面完成度不足的问题，补充了帮助页面并统一了页面视觉风格。'
    ]
  },
  {
    index: '06',
    title: '注意事项',
    description: '正式演示前，建议快速检查以下内容。',
    items: [
      '确保 Flask、FastAPI 和前端都已经启动成功。',
      '提前准备一张图片和一个较短视频作为演示素材。',
      '确认摄像头权限已开启，实时检测页面可以正常访问设备。',
      '如果需要展示报告导出，提前做一两条检测记录作为样例数据。'
    ]
  }
]
</script>

<style scoped>
.help-hero {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 28px;
  border-radius: 30px;
}

.help-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.help-card {
  position: relative;
  padding: 24px;
  overflow: hidden;
}

.card-index {
  position: absolute;
  top: 18px;
  right: 20px;
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
  color: rgba(14, 116, 144, 0.12);
}

.help-card h2 {
  position: relative;
  margin: 0 0 10px;
  font-size: 23px;
  color: var(--text-main);
}

.card-description {
  position: relative;
  margin: 0 0 16px;
  color: var(--text-muted);
  line-height: 1.7;
}

.help-card ul {
  position: relative;
  display: grid;
  gap: 12px;
  margin: 0;
  padding-left: 20px;
}

.help-card li {
  color: var(--text-main);
  line-height: 1.7;
}

@media (max-width: 900px) {
  .help-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .help-hero,
  .help-card {
    padding: 20px;
  }

  .card-index {
    font-size: 34px;
  }
}
</style>
