package app;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import org.apache.commons.math3.distribution.AbstractRealDistribution;
import org.apache.commons.math3.distribution.ExponentialDistribution;

import Server.MCAtomicUpdater;
import Server.SimpleTask;
import net.spy.memcached.MemcachedClient;

public class Client implements Runnable {

	private SimpleTask task = null;
	private ExponentialDistribution dist = null;
	private long thinkTime = -1;
	private UUID clietId = null;
	public static AtomicInteger time = new AtomicInteger(0);
	private MemcachedClient memcachedClient = null;
	private static AtomicInteger toKill = new AtomicInteger(0);
	private Boolean dying = false;
	private static String tier1Host = null;

	public Client(SimpleTask task, Long ttime) {
		this.setThinkTime(ttime);
		this.task = task;
		this.clietId = UUID.randomUUID();
		try {
			this.memcachedClient = new MemcachedClient(new InetSocketAddress(this.task.getJedisHost(), 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public void run() {
		try {
			HttpClient client = null;
			HttpRequest request = null;
			client = HttpClient.newBuilder().version(Version.HTTP_1_1).build();
			request = HttpRequest.newBuilder().uri(URI.create("http://" + Client.getTier1Host() + ":3000/?id="
					+ this.clietId.toString() + "&entry=e1" + "&snd=think")).build();

			this.memcachedClient.set("started", 3600, String.valueOf(1)).get();
			MCAtomicUpdater.AtomicIncr(this.memcachedClient, 1, "think", 100);

			while ((this.memcachedClient.get("stop") == null
					|| !String.valueOf(this.memcachedClient.get("stop")).equals("1")) && !this.dying) {

//				String thinking = String.valueOf(this.memcachedClient.get("think"));

//				SimpleTask.getLogger().debug(String.format("stop=%s", String.valueOf(memcachedClient.get("stop"))));
				TimeUnit.MILLISECONDS.sleep(Double.valueOf(this.dist.sample()).longValue());

//				SimpleTask.getLogger().debug(String.format("%s sending", this.task.getName()));
				HttpResponse<String> resp = client.send(request, BodyHandlers.ofString());

				// long thinking = this.memcachedClient.incr("think", 1);
//				MCAtomicUpdater.AtomicIncr(this.memcachedClient, -1, "e1_ex", 100);
//				MCAtomicUpdater.AtomicIncr(this.memcachedClient, 1, "think", 100);

//				SimpleTask.getLogger().debug(String.format("%s thinking", thinking));
				
//				if (Client.getToKill().get() > 0) {
//					Client.toKill.decrementAndGet();
//					this.dying = true;
//				}
			}
			MCAtomicUpdater.AtomicIncr(this.memcachedClient, -1, "think", 100);
			SimpleTask.getLogger().debug(String.format(" user %s stopped", this.clietId));
		} catch (IOException e1) {
			e1.printStackTrace();
		} catch (InterruptedException e2) {
			e2.printStackTrace();
		} catch (Exception e) {
			e.printStackTrace();
		} finally {
			this.memcachedClient.shutdown();
		}
	}

	public long getThinkTime() {
		return this.thinkTime;
	}

	public AbstractRealDistribution getTtimeDist() {
		return this.dist;
	}

	public void setThinkTime(long thinkTime) {
		this.thinkTime = thinkTime;
		this.dist = new ExponentialDistribution(thinkTime);
	}

	public static AtomicInteger getToKill() {
		return toKill;
	}

	public static void setToKill(Integer toKill) {
		Client.toKill.addAndGet(toKill);
	}

	public static String getTier1Host() {
		return tier1Host;
	}

	public static void setTier1Host(String tier1Host) {
		Client.tier1Host = tier1Host;
	}

}
