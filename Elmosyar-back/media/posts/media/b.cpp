#include<bits/stdc++.h>
#define int long long
#define pii pair<int, int>
#define f0 first
#define s0 second
#define pb push_back
using namespace std;

int constexpr maxn = 200009, mod = 1e9 + 7, inf = (1LL << 60);

int n, m, k;

void ready(){
    return;
}

void preprocess(){
    return;
}

int f(int k, int idx, vector<int> &a, vector<int> &b){
    int res = 0;
    for(int i = 1; i <= k; ++i){
        int sum = 0;
        for(int j = idx; j + i < n; ++j)
            sum += (int)(b[j] == a[j + i]);
        res = max(res, sum);
    }
    return res;
}

int g(int k, int idx, vector<int> &a, vector<int> &b){
    int res = 0;
    for(int i = 1; i <= k; ++i){
        int sum = 0;
        for(int j = idx; j < n; ++j)
            sum += (int)(b[j] == a[j - i]);
        res = max(res, sum);
    }
    return res;
}

void give_input(){
    string s;
    cin >> n >> m;
    vector<char> a(n, '0'), b(n, '0');
    for(int i = 0; i < n; ++i)
        cin >> a[i];
    for(int i = 0; i < m; ++i){
        int num;
        char c;
        cin >> num >> c;
        b[num - 1] = c;
    }
    int k = 0;
    bool bg = true;
    vector<vector<int>> v;
    vector<int> score;
    for(int i = 0; i < n; ++i){
        if(bg == true && b[i] == '0'){
            v.push_back({i, 1});
        }
        else if(bg == false && b[i] == '0'){
            v.back()[1] += 1;
        }
        else if(b[i] != '0'){
            bg = true;
        }
        if(i){
            score.push_back(score.back() + (int)(b[i] == a[i]));
        }
        else{
            score.push_back((int)(b[i] == a[i]));
        }
    }
    int ans = score[n - 1];
    if(b[n - 1] == '0'){
        for(int i = 0; i < n; ++i){
            if(b[i] != '0'){
                int calc = f(v.back()[1], i, a, b);
                ans = max(ans, (i ? score[i - 1] : 0) + calc);
            }
        }
    }
    ///////////////////
    /////////////////////
    //////////////////
    //////////////////////
    bg = true;
    int cnt = 0;
    for(int i = 0; i < n; ++i){
        if(bg == true && b[i] == '0'){
            if(v[cnt][1] + i >= n - 1){
                ++cnt;
                continue;
            }
            int calc = g(v[cnt][1], i + v[cnt][1], a, b);
            if(v[cnt][1] + i < n - 1)
            ans = max(ans, (i ? score[i - 1] : 0) + calc);
            ++cnt;
        }
        else if(bg == false && b[i] == '0'){}
        else if(b[i] != '0'){
            bg = true;
        }
    }
    cout << ans << '\n';
    return;
}

void process(){
    return;
}

void get_output(){
    return;
}

signed main(){
    ios::sync_with_stdio(0), cin.tie(0);
    int t = 1;
	cin >> t;
	preprocess();
    while(t--){
        give_input();
        process();
        get_output();
        ready();
    }
    return 0;
}