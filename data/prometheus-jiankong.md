# Prometheus 监控入门

## Prometheus 是什么
Prometheus 是开源的系统监控与告警工具，采用拉（pull）模型定期抓取暴露的指标。它适合云原生环境下的指标监控。

## 指标类型
Counter 只增计数器，Gauge 可增可减，Histogram 观察分布，Summary 计算分位数。选择合适的指标类型对监控很重要。

## 抓取配置
在 prometheus.yml 里用 scrape_configs 配置抓取目标，job_name 标识一组目标，static_configs 列出实例地址。每个实例都要暴露 /metrics 接口。

## 查询语言 PromQL
PromQL 用 rate(http_requests_total[5m]) 计算每秒请求速率，up 指标表示实例是否在线。PromQL 还支持聚合和前缀匹配。

## 告警
Alertmanager 负责把 Prometheus 产生的告警去重、分组并路由到邮件或钉钉等接收方。告警规则写在 Prometheus 的 rules 文件里。
