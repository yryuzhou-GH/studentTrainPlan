var domCourse = document.getElementById("course_box");
var domPerson = document.getElementById("person_box");
var chartCourse = echarts.init(domCourse);
var chartPerson = echarts.init(domPerson);
var app = {};
optionCourse = null;
optionPerson = null;

// 定义获取推荐数据的函数，方便刷新时调用
function fetchRecommendData() {
    // 显示加载状态
    var loadingOption = {
        title: {
            text: '正在加载推荐数据...',
            left: 'center',
            top: 'middle',
            textStyle: {
                fontSize: 16,
                color: '#666'
            }
        }
    };
    chartCourse.setOption(loadingOption, true);
    chartPerson.setOption(loadingOption, true);
    
    $.ajax({
    url: '/getRecommedData',
    type: 'GET',
    dataType: 'json',
    success: function(coursePersonJson) {
        console.log('收到推荐数据:', coursePersonJson);
        
        // 检查数据是否存在
        if (!coursePersonJson) {
            console.error('推荐数据为空');
            return;
        }
        
        // 检查课程数据
        if (!coursePersonJson['course'] || !coursePersonJson['course']['source']) {
            console.error('课程推荐数据格式错误:', coursePersonJson['course']);
            return;
        }
        
        // 检查学生数据
        if (!coursePersonJson['person'] || !coursePersonJson['person']['source']) {
            console.error('学生推荐数据格式错误:', coursePersonJson['person']);
            return;
        }
        
        console.log('课程数据:', coursePersonJson['course']['source']);
        console.log('学生数据:', coursePersonJson['person']['source']);
        
        // 配置课程推荐图表
        var optionCourse = {
            dataset: coursePersonJson['course'],
            grid: {containLabel: true},
            xAxis: {name: '喜爱程度'},
            yAxis: {type: 'category'},
            visualMap: {
                orient: 'horizontal',
                left: 'center',
                min: 1,
                max: 5,
                text: ['High Score', 'Low Score'],
                // Map the score column to color
                dimension: 0,
                inRange: {
                    color: ['#D7DA8B', '#E15457']
                }
            },
            series: [
                {
                    type: 'bar',
                    encode: {
                        // Map the "amount" column to X axis.
                        x: 'amount',
                        // Map the "product" column to Y axis
                        y: 'product'
                    }
                }
            ]
        };
        
        // 配置学生推荐图表
        var optionPerson = {
            dataset: coursePersonJson['person'],
            grid: {containLabel: true},
            xAxis: {name: '相似度'},
            yAxis: {type: 'category'},
            visualMap: {
                orient: 'horizontal',
                left: 'center',
                min: 0,
                max: 1,
                text: ['High Score', 'Low Score'],
                // Map the score column to color
                dimension: 0,
                inRange: {
                    color: ['#D7DA8B', '#E15457']
                }
            },
            series: [
                {
                    type: 'bar',
                    encode: {
                        // Map the "amount" column to X axis.
                        x: 'amount',
                        // Map the "product" column to Y axis
                        y: 'product'
                    }
                }
            ]
        };
        
        // 检查数据是否为空（只有列名）
        if (coursePersonJson['course']['source'].length <= 1) {
            console.warn('课程推荐数据为空，只显示空图表');
            // 显示提示信息
            optionCourse.title = {
                text: '暂无课程推荐数据',
                left: 'center',
                top: 'middle',
                textStyle: {
                    fontSize: 16,
                    color: '#999'
                }
            };
        }
        
        if (coursePersonJson['person']['source'].length <= 1) {
            console.warn('学生推荐数据为空，只显示空图表');
            // 显示提示信息
            optionPerson.title = {
                text: '暂无相似学生数据',
                left: 'center',
                top: 'middle',
                textStyle: {
                    fontSize: 16,
                    color: '#999'
                }
            };
        }
        
        // 设置图表选项
        if (optionCourse && typeof optionCourse === "object") {
            chartCourse.setOption(optionCourse, true);
            console.log('课程图表已更新');
        }
        if (optionPerson && typeof optionPerson === "object") {
            chartPerson.setOption(optionPerson, true);
            console.log('学生图表已更新');
        }
    },
    error: function(xhr, status, error) {
        console.error('获取推荐数据失败:', status, error);
        console.error('响应内容:', xhr.responseText);
        
        // 显示错误信息
        var errorOption = {
            title: {
                text: '加载推荐数据失败',
                subtext: '请刷新页面重试',
                left: 'center',
                top: 'middle',
                textStyle: {
                    fontSize: 16,
                    color: '#f56c6c'
                }
            }
        };
        chartCourse.setOption(errorOption, true);
        chartPerson.setOption(errorOption, true);
    }
    });
}

// 页面加载时获取推荐数据
fetchRecommendData();

// 将刷新函数暴露到全局，方便外部调用
window.refreshRecommendData = fetchRecommendData;
