const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

async function testAPIFlow() {
    console.log('🔍 Testing API Flow...\n');
    
    // Test 1: FastAPI Backend Direct
    console.log('1. Testing FastAPI Backend (localhost:8000)...');
    try {
        const backendResponse = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                aiConfigKey: 'toggle-rag',
                userInput: 'test metrics'
            })
        });
        
        if (backendResponse.ok) {
            const backendData = await backendResponse.json();
            console.log('✅ Backend Response:', {
                hasResponse: !!backendData.response,
                hasModelName: !!backendData.modelName,
                hasMetrics: !!backendData.metrics,
                metricsKeys: backendData.metrics ? Object.keys(backendData.metrics) : []
            });
            
            if (backendData.metrics) {
                console.log('📊 Backend Metrics Sample:', {
                    grounding_score: backendData.metrics.grounding_score,
                    relevance_score: backendData.metrics.relevance_score,
                    processing_latency_ms: backendData.metrics.processing_latency_ms
                });
            }
        } else {
            console.log('❌ Backend Error:', backendResponse.status, backendResponse.statusText);
        }
    } catch (error) {
        console.log('❌ Backend Connection Error:', error.message);
    }
    
    console.log('\n' + '='.repeat(50) + '\n');
    
    // Test 2: Next.js API Route
    console.log('2. Testing Next.js API Route (localhost:3000)...');
    try {
        const nextResponse = await fetch('http://localhost:3000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                aiConfigKey: 'toggle-rag',
                userInput: 'test metrics'
            })
        });
        
        if (nextResponse.ok) {
            const nextData = await nextResponse.json();
            console.log('✅ Next.js Response:', {
                hasResponse: !!nextData.response,
                hasModelName: !!nextData.modelName,
                hasMetrics: !!nextData.metrics,
                metricsKeys: nextData.metrics ? Object.keys(nextData.metrics) : []
            });
            
            if (nextData.metrics) {
                console.log('📊 Next.js Metrics Sample:', {
                    grounding_score: nextData.metrics.grounding_score,
                    relevance_score: nextData.metrics.relevance_score,
                    processing_latency_ms: nextData.metrics.processing_latency_ms
                });
            }
            
            // Compare with backend
            console.log('\n🔍 Comparison:', {
                metricsPassedThrough: !!nextData.metrics,
                bothHaveMetrics: !!nextData.metrics
            });
        } else {
            console.log('❌ Next.js Error:', nextResponse.status, nextResponse.statusText);
        }
    } catch (error) {
        console.log('❌ Next.js Connection Error:', error.message);
    }
    
    console.log('\n' + '='.repeat(50) + '\n');
    console.log('🎯 Summary:');
    console.log('- If both show ✅ and have metrics, the API flow is working');
    console.log('- If metrics are missing in Next.js, check pages/api/chat.ts');
    console.log('- If frontend still not showing metrics, check React component state/rendering');
    console.log('\nCheck the browser console for React component debug logs!');
}

testAPIFlow().catch(console.error); 